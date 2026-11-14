"""Report saved evidence only; no model, controller, estimator, or audit rerun.

Each attempt has its own append-only report. Summary flags describe the recorded
run conclusion; stage claims additionally require files from that attempt.
"""
import csv
from collections import Counter
import json
from pathlib import Path
from .common import read_json, sha_file, safe_label

ROOT = Path(__file__).resolve().parents[2]
PHASE_NAMES = {
    'supervision': '监管准入', 'isolation': '隔离准入', 'interface': '在线接口准入',
    'interface_failure': '接口故障准入', 'short': '短检查', 'regression': '选定回归',
    'initialize': '主回合初始化', 'primary': '主候选评价', 'select': '精确选择',
    'actual': '主回合实际执行', 'reference': '独立候选参照', 'audit': '保存结果审计',
}


def _read_optional(path, warnings):
    if not path.is_file():
        return None
    try:
        return read_json(path)
    except (OSError, ValueError) as error:
        warnings.append(f'{path}: {type(error).__name__}: {error}')
        return None


def _saved_path(attempt, value, warnings):
    """Do not borrow results from another attempt through a stored path."""
    if not isinstance(value, str) or not value:
        return None
    p = Path(value)
    p = (p if p.is_absolute() else attempt/p).resolve()
    if not p.is_relative_to(attempt):
        warnings.append('忽略当前attempt之外的证据引用：'+str(p))
        return None
    return p


def _counter(value):
    return value if type(value) is int and value >= 0 else None


def _number(value):
    return value if type(value) in (int, float) else None


def _format_number(value, digits=6):
    value = _number(value)
    return '未记录' if value is None else f'{value:.{digits}f}'


def _cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def _classification(result):
    numerical = result.get('numerical_and_contract_passed') is True
    if numerical and result.get('passed') is True and result.get('research_coverage_passed') is True:
        return 'FULL_PASS'
    if numerical and result.get('passed') is False and result.get('research_coverage_passed') is False:
        return 'NUMERICAL_PASS_COVERAGE_GAP'
    return 'STOPPED_OR_INCOMPLETE'


def _collect(attempt, result, ledger):
    """Collect completed and partial records without re-evaluating any result."""
    warnings = []
    jobs = ledger.get('jobs', [])
    if not isinstance(jobs, list):
        raise ValueError('resource_ledger.jobs must be a list')
    phases = Counter(row.get('phase', 'unknown') for row in jobs)
    accepted_phases = Counter(row.get('phase', 'unknown') for row in jobs if row.get('accepted') is True)
    accepted_outputs = {str((attempt/'pairs'/safe_label(row['pair_id'])/'env/result.json').resolve())
                        for row in jobs if row.get('accepted') is True}
    counts = dict(real_wls=0, starts=0, regression_wls=0, regression_starts=0,
                  counter_sources=[], missing_scientific_counter_files=[])
    short_passed, short_attempted = set(), set()
    regression_tests = 0
    partial_items = {'primary': 0, 'reference': 0}
    failed_states = []
    sampling_files = []
    worker_failures = []
    for job in jobs:
        phase = job.get('phase', 'unknown')
        base = attempt/'pairs'/safe_label(job['pair_id'])
        counter_path = base/'sense/counters.json'
        c = _read_optional(counter_path, warnings)
        if isinstance(c, dict):
            calls, starts = _counter(c.get('estimator_calls')), _counter(c.get('start_attempts'))
            if calls is None or starts is None:
                warnings.append('感知计数缺失或类型无效：'+str(counter_path))
            else:
                counts['real_wls'] += calls
                counts['starts'] += starts
                counts['counter_sources'].append(dict(path=str(counter_path), pair_id=job['pair_id'],
                    phase=phase, accepted=job.get('accepted') is True, real_wls=calls, starts=starts))
        elif phase in ('short', 'primary', 'reference', 'actual'):
            counts['missing_scientific_counter_files'].append(str(counter_path))
        if phase == 'regression':
            counter_path = base/'env/estimate_counts.json'
            c = _read_optional(counter_path, warnings)
            if isinstance(c, dict):
                calls, starts = _counter(c.get('real_estimates')), _counter(c.get('native_start_attempts'))
                if calls is None or starts is None:
                    warnings.append('回归计数缺失或类型无效：'+str(counter_path))
                else:
                    counts['regression_wls'] += calls
                    counts['regression_starts'] += starts
                    counts['counter_sources'].append(dict(path=str(counter_path), pair_id=job['pair_id'],
                        phase=phase, accepted=job.get('accepted') is True, real_wls=calls, starts=starts))
            else:
                counts['missing_scientific_counter_files'].append(str(counter_path))
            saved = _read_optional(base/'env/result.json', warnings)
            if job.get('accepted') is True and isinstance(saved, dict) and saved.get('passed') is True:
                regression_tests += _counter(saved.get('tests')) or 0
        if phase == 'short':
            for folder in sorted((base/'env').glob('S[0-9][0-9]')):
                if not folder.is_dir():
                    continue
                short_attempted.add(folder.name)
                saved = _read_optional(folder/'result.json', warnings)
                if isinstance(saved, dict) and saved.get('passed') is True and saved.get('check_id') == folder.name:
                    short_passed.add(folder.name)
        if phase in partial_items:
            saved = _read_optional(base/'env/completed_items.json', warnings)
            if isinstance(saved, list):
                partial_items[phase] += len(saved)
        if phase in ('initialize', 'actual'):
            for name in ('failed_private_snapshot.json', 'last_committed_state.json'):
                path = base/'env'/name
                if path.is_file():
                    failed_states.append(dict(pair_id=job['pair_id'], accepted=job.get('accepted') is True,
                                              path=str(path), kind=name))
            path = base/'env/actual_sampling_journal.json'
            if path.is_file():
                sampling_files.append(str(path))
        failure = _read_optional(base/'env/failure.json', warnings)
        if isinstance(failure, dict) and job.get('accepted') is not True:
            worker_failures.append(dict(pair_id=job['pair_id'], phase=phase,
                error_type=failure.get('error_type', failure.get('type')),
                error=failure.get('error', failure.get('message')), path=str(base/'env/failure.json')))
    counts['real_wls'] += counts['regression_wls']
    counts['starts'] += counts['regression_starts']
    registry_path = attempt/'actual_checkpoint_registry.json'
    registry = _read_optional(registry_path, warnings)
    registry = registry if isinstance(registry, list) else []
    seal_files = sorted((attempt/'checkpoint_seals').glob('*.json'))
    index_paths = set((attempt/'episode_indices').glob('*.json'))
    for value in result.get('episode_index_files', []):
        path = _saved_path(attempt, value, warnings)
        if path is not None:
            index_paths.add(path)
    episodes, decisions = [], []
    for path in sorted(index_paths):
        index = _read_optional(path, warnings)
        if not isinstance(index, dict):
            continue
        audit_path = _saved_path(attempt, index.get('episode_audit_file'), warnings)
        audit = _read_optional(audit_path, warnings) if audit_path else None
        audited = (isinstance(audit, dict) and audit.get('passed') is True
                   and str(audit_path) in accepted_outputs)
        episode = dict(episode_id=index.get('episode_id', path.stem), index_file=str(path),
                       recorded_decision_intervals=len(index.get('decisions', [])),
                       accepted_episode_audit=audited, audit_file=str(audit_path) if audit_path else None,
                       audit=audit if audited else None)
        episodes.append(episode)
        for d in index.get('decisions', []):
            sel_path = _saved_path(attempt, d.get('selection_file'), warnings)
            step_path = _saved_path(attempt, d.get('step_result_file'), warnings)
            sel = _read_optional(sel_path, warnings) if sel_path else None
            step = _read_optional(step_path, warnings) if step_path else None
            if not isinstance(sel, dict) or not isinstance(step, dict):
                warnings.append(f'{path}: tick {d.get("tick")} 缺少选择或实际step结果')
                continue
            metrics = step.get('metrics', {})
            decisions.append(dict(episode=episode['episode_id'], tick=d.get('tick'),
                candidate_count=sel.get('candidate_count'), selected_indices=sel.get('selected_indices'),
                actions=sel.get('actions'), prediction_value=sel.get('table_value_float'),
                actual_cumulative_return=metrics.get('return_with_changes'),
                actual_change_count=metrics.get('assignment_changes'),
                evidence_status='ACCEPTED_EPISODE_AUDIT' if audited else 'SAVED_NOT_EPISODE_AUDITED',
                selection_file=str(sel_path), step_result_file=str(step_path)))
    authorization = _read_optional(attempt/'authorization.json', warnings)
    prior_attempt = authorization.get('prior_attempt') if isinstance(authorization, dict) else None
    return dict(prior_attempt=prior_attempt if isinstance(prior_attempt, str) else None, jobs=jobs, phases=dict(phases), accepted_phases=dict(accepted_phases), counts=counts,
                short_passed=sorted(short_passed), short_attempted=sorted(short_attempted),
                regression_tests=regression_tests, completed_item_records=partial_items,
                registry=registry, checkpoint_seals=[str(p) for p in seal_files], episodes=episodes,
                decisions=decisions, actual_state_files=failed_states, actual_sampling_files=sampling_files,
                worker_failures=worker_failures, warnings=warnings)


def _render(attempt, result, ledger, evidence, seal):
    state = _classification(result)
    numerical = result.get('numerical_and_contract_passed') is True
    phases = evidence['phases']; jobs = evidence['jobs']; counts = evidence['counts']
    accepted = sum(j.get('accepted') is True for j in jobs)
    audited = [e for e in evidence['episodes'] if e['accepted_episode_audit']]
    registry = evidence['registry']
    actual_started = phases.get('actual', 0)
    titles = {'FULL_PASS': '**数值、合同与研究见证验收通过。**',
              'NUMERICAL_PASS_COVERAGE_GAP': '**数值与合同验收通过，但规定的研究见证未全部获得。**',
              'STOPPED_OR_INCOMPLETE': '**本轮停止或记录不完整，尚未通过完整验收。**'}
    relative = str(attempt.relative_to(ROOT)) if attempt.is_relative_to(ROOT) else str(attempt)
    lines = ['# 2A-5b 小规模自主GQ闭环验收报告', '',
             f"协议：STAGE2A5B-GQ-ONLINE-v1.0，准备包{_cell(seal.get('preparation_revision', '未记录'))}。", f'运行目录：`{relative}`', '',
             '## 1. 本轮实际状态', '', titles[state], '']
    if evidence.get('prior_attempt'):
        lines += [f"本attempt的修复来源由authorization.prior_attempt记录为：`{evidence['prior_attempt']}`。旧attempt与旧报告独立保留；下列计数只汇总当前attempt，不覆盖或混入旧运行。", '']
    if state == 'FULL_PASS':
        lines += ['运行总结果记录数值、合同和研究覆盖均通过；各回合结果与证据范围见下文。', '']
    elif state == 'NUMERICAL_PASS_COVERAGE_GAP':
        lines += ['运行总结果记录完整数值与合同检查通过，但未获得全部规定见证；不将合法最优选择自动解释为研究目标全部完成。', '']
    elif not any(phases.get(p, 0) for p in ('initialize', 'primary', 'select', 'actual')) and not registry:
        lines += ['现有监管记录停留在主回合之前的准入、短检查或回归阶段；没有主回合初始化、候选评价或实际推进的job记录。短检查合成状态不是真实回合checkpoint。', '']
    elif actual_started == 0:
        lines += ['已进入主回合准备、初始化或评分阶段，但没有主回合实际执行job记录；已保存的预测或选择不能作为实际推进结果。', '']
    else:
        lines += [f'已进入主回合实际执行阶段，共有{actual_started}个相关监管job记录。仅报告已保存的实际状态和结果；没有完整验收时，不把部分执行称为闭环通过。', '']
    if state == 'STOPPED_OR_INCOMPLETE':
        last = result.get('last_job') or (jobs[-1] if jobs else {})
        if result.get('error_type') or result.get('error'):
            lines += [f"停止原因：`{_cell(result.get('error_type', '未记录'))}: {_cell(result.get('error', '未记录'))}`。", '']
        else:
            lines += [f"结果状态：`{_cell(result.get('status', '未记录'))}`；未保存明确停止原因。", '']
        lines += [f"最后记录job：`{_cell(last.get('pair_id', '无记录'))}`，阶段`{_cell(last.get('phase', '未记录'))}`。", '']
        for failure in evidence['worker_failures'][-1:]:
            lines += [f"该失败分支保存的worker异常：`{_cell(failure['error_type'])}: {_cell(failure['error'])}`。来源：`{failure['path']}`。", '']
        if result.get('automatic_retry') is False:
            lines += ['运行结果明确记录automatic_retry=false；本报告只读取保存记录，没有重跑科学计算。', '']
    lines += ['## 2. 覆盖、资源与计算范围', '',
        f"运行摘要记录的完整实际决策区间：{result.get('actual_decisions', '未记录')}/30；主候选评价：{result.get('primary_candidate_evaluations', '未记录')}；独立候选参照：{result.get('independent_candidate_evaluations', '未记录')}。", '',
        f"另从completed_items.json读取到主候选输出{evidence['completed_item_records']['primary']}项、独立参照输出{evidence['completed_item_records']['reference']}项；它们可能包含中途失败批次已写出的部分结果，不等于完整表或审计通过数。", '',
        f'接受job：{accepted}/{len(jobs)}（按resource_ledger逐行统计）。接受数包含符合预期的负探针；raw_passed与accepted分别保留，不将负探针原始失败改写为正常科学成功。', '',
        '| 阶段 | 已有监管job | 接受job |', '| --- | ---: | ---: |']
    for phase, label in PHASE_NAMES.items():
        lines.append(f"| {label} | {phases.get(phase, 0)} | {evidence['accepted_phases'].get(phase, 0)} |")
    resources = result.get('resource', {})
    cpu = resources.get('scientific_cpu', ledger.get('worker_cpu'))
    wall = resources.get('wall', ledger.get('wall'))
    lines += ['', f'全轮已记录科学CPU：{_format_number(cpu)}/1200秒；墙钟：{_format_number(wall)}/2400秒。', '',
              'CPU范围为本attempt实际启动并记账的科学worker完整生命周期，包含失败job；未启动阶段不算作已执行。controller与guardian单列，不据此声称实时能力。', '',
              f"已保存计数文件合计WLS {counts['real_wls']}次、局部起点{counts['starts']}次；协议上限为25357/228213。其中回归WLS {counts['regression_wls']}次，mock和求解前拒绝不计入WLS。失败job的现存计数也纳入合计。", '',
              '计数来源逐文件保存在delivery/count_summary.json；缺失或损坏记录不补零，也不把空缺当作未调用的证明。', '',
              f"短检查已有独立通过记录{len(evidence['short_passed'])}/30：{', '.join(evidence['short_passed']) or '无'}。已创建检查目录但尚无通过记录：{', '.join(sorted(set(evidence['short_attempted'])-set(evidence['short_passed']))) or '无'}。", '',
              f"已接受且result.passed=true的回归批合计{evidence['regression_tests']}/132项；预声明数量不代替实际结果。", '',
              '| job | 阶段 | raw_passed | 接受 | 科学CPU（秒） |', '| --- | --- | --- | --- | ---: |']
    for row in jobs:
        lines.append(f"| {_cell(row['pair_id'])} | {_cell(row.get('phase'))} | {_cell(row.get('raw_passed', '未记录'))} | {'是' if row.get('accepted') is True else '否'} | {_format_number(row.get('worker_cpu'))} |")
    lines += ['', '## 3. 主回合实际记录与审计状态', '',
        f"当前attempt的实际checkpoint登记表包含{len(registry)}条记录，checkpoint_seals中有{len(evidence['checkpoint_seals'])}份文件；该数量不包括短检查的合成checkpoint。", '']
    if not registry:
        lines += ['当前没有已登记的主回合实际checkpoint，不能声称主回合状态保存/恢复或真实历史验收已经完成。', '']
    else:
        cuts = {}
        for row in registry:
            cuts.setdefault(str(row.get('episode_id')), []).append(row.get('tick'))
        lines += [f"实际登记的cut：{'; '.join(k+': '+', '.join(map(str,v)) for k,v in cuts.items())}。", '']
    if evidence['episodes']:
        lines += ['| 回合 | 索引内实际区间数 | 已接受的回合审计 | 研究覆盖 |', '| --- | ---: | --- | --- |']
        for row in evidence['episodes']:
            a = row['audit']
            coverage = ('通过' if a.get('all_episode_objectives_passed') is True else '见证不足') if a else '未形成已接受结论'
            lines.append(f"| {_cell(row['episode_id'])} | {row['recorded_decision_intervals']} | {'是' if a else '否'} | {coverage} |")
        lines.append('')
    if audited:
        lines += ['以下数值仅摘录已接受的回合审计文件：', '',
                  '| 回合 | 完成释放事件数 | 实际净O | 控制积分 | 占用机器人秒 |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for row in audited:
            a = row['audit']; m = a.get('metrics', {}); coverage = a.get('coverage', {})
            completions = coverage.get('actual_completion_releases')
            count = len(completions) if isinstance(completions, list) else '未记录'
            lines.append(f"| {_cell(row['episode_id'])} | {count} | {_format_number(m.get('return_with_changes'),12)} | {_format_number(m.get('control_integral'),12)} | {_format_number(m.get('occupied_robot_seconds'))} |")
        lines += ['', '这些回合的实际轨迹和收益已有保存的独立审计结论；其他回合不据此推定通过。', '']
    else:
        lines += ['未取得任何已接受的完整回合审计结论；本报告不声称实际回合收益已经独立重建。', '']
    if not numerical:
        lines += ['当前没有完整数值与合同验收结论。保存的部分选择、控制帧或累计费用仅作失败定位，不能作为闭环成功证据。', '']
    pair_path = _saved_path(attempt, result.get('paired_future_audit'), evidence['warnings'])
    pair_audit = _read_optional(pair_path, evidence['warnings']) if pair_path else None
    if isinstance(pair_audit, dict) and pair_audit.get('passed') is True and str(pair_path) in {
            str((attempt/'pairs'/safe_label(j['pair_id'])/'env/result.json').resolve()) for j in jobs if j.get('accepted') is True}:
        lines += ['N4隐藏未来配对已有接受的审计结果；该结论仅覆盖其保存的配对检查范围。', '']
    else:
        lines += ['本报告未读取到已接受的N4隐藏未来配对审计结果，不宣称该项通过。', '']
    protocol_sha = seal.get('protocol_lock_sha256')
    lines += ['## 4. 源码、输入与证据来源', '',
              f"本attempt封存I记录的准备包SHA256：`{protocol_sha or '未记录'}`。本项不读取ROOT中未来可能更新的锁文件作为旧运行身份。", '',
              f"本attempt运行封存I文件SHA256：`{sha_file(attempt/'SEAL_I.json') if (attempt/'SEAL_I.json').is_file() else '未保存'}`。", '']
    protection = result.get('old_protection')
    if isinstance(protection, dict):
        lines += [f"结果文件记录的旧源保护结论：passed=`{protection.get('passed', '未记录')}`。详见本attempt的protection_before、result及实际存在的protection_after；本报告没有重新执行保护核验。", '']
    else:
        lines += ['结果中没有完整旧源保护结论；不能仅凭保护清单存在宣称本轮核验通过。', '']
    lines += [f"主回合实际状态/失败快照文件记录{len(evidence['actual_state_files'])}份，实际采样日志文件{len(evidence['actual_sampling_files'])}份。路径列于delivery/evidence_summary.json；文件存在不等于已经独立审计通过。", '',
              '各阶段只引用本attempt实际保存的文件；历史报告和旧attempt均未修改。本报告生成过程不调用控制器、WLS、候选评价或独立科学审计。', '']
    if evidence['warnings'] or counts['missing_scientific_counter_files']:
        lines += ['证据读取/计数缺口：', '']
        lines += ['- '+_cell(w) for w in evidence['warnings']]
        lines += ['- 未找到该阶段计数文件：`'+p+'`' for p in counts['missing_scientific_counter_files']]
        lines.append('')
    lines += ['## 5. 结论边界', '',
              '本协议面向确定性小规模架构核验。Q是声明不确定度的局部代理，不能等同实际定位误差或随机可靠性；本报告没有新增实时性能、估计反馈控制或无缝交接结论。', '',
              '有限候选表的选择不能合成为整回合最优，也没有据此证明G-only收益是GQ上界。实际回合收益只引用上文已接受的审计记录，不累计相互重叠的预测窗口值。', '',
              '后续判断应依据本attempt实际完成的阶段和仍未覆盖的项目；失败记录与局限保留。', '']
    return '\n'.join(lines), state


def _write_json_exclusive(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def report(attempt):
    attempt = Path(attempt).resolve()
    result = read_json(attempt/'result.json')
    ledger_path = attempt/'resource_ledger.json'
    ledger = read_json(ledger_path) if ledger_path.is_file() else {'jobs': []}
    seal = read_json(attempt/'SEAL_I.json') if (attempt/'SEAL_I.json').is_file() else {}
    evidence = _collect(attempt, result, ledger)
    if not ledger_path.is_file():
        evidence['warnings'].append('resource_ledger.json未保存；不能确认job覆盖和完整成本账。')
    markdown, state = _render(attempt, result, ledger, evidence, seal)
    # Full attempt basename is retained. Never update the legacy aggregate report.
    label = safe_label(attempt.name)
    if not label or label != attempt.name:
        raise ValueError('Attempt basename must be an unambiguous safe report label')
    path = ROOT/'docs'/f'STAGE2A5B_GQ_ONLINE_VALIDATION_{label}.md'
    delivery = attempt/'delivery'
    outputs = [path, delivery/'VALIDATION.md', delivery/'count_summary.json',
               delivery/'decision_summary.json', delivery/'evidence_summary.json']
    if evidence['decisions']:
        outputs.append(delivery/'decision_summary.csv')
    # Check every output before creating anything, then use exclusive writes too.
    for output in outputs:
        if output.exists():
            raise FileExistsError('Never overwrite existing report evidence: '+str(output))
    delivery.mkdir(exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as out:
        out.write(markdown)
    with (delivery/'VALIDATION.md').open('x', encoding='utf-8', newline='\n') as out:
        out.write(markdown)
    _write_json_exclusive(delivery/'count_summary.json', evidence['counts'])
    _write_json_exclusive(delivery/'decision_summary.json', evidence['decisions'])
    summary = {k:v for k,v in evidence.items() if k not in ('episodes','decisions')}
    summary['episodes'] = [{k:v for k,v in row.items() if k != 'audit'} for row in evidence['episodes']]
    summary.update(report_classification=state, result_status=result.get('status'))
    _write_json_exclusive(delivery/'evidence_summary.json', summary)
    if evidence['decisions']:
        with (delivery/'decision_summary.csv').open('x', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=list(evidence['decisions'][0]))
            writer.writeheader()
            writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v
                              for k,v in row.items()} for row in evidence['decisions'])
    return dict(passed=state == 'FULL_PASS', recorded_run_passed=result.get('passed') is True, report_classification=state,
                report=str(path), delivery=str(delivery), real_wls=evidence['counts']['real_wls'],
                starts=evidence['counts']['starts'], evidence_warnings=evidence['warnings'])
