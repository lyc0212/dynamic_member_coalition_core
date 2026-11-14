"""Figures from saved execution/audit arrays; no WLS or simulator calls.

Figure claim: the declared Q interventions alter actual service termination and
the resulting motion/resource lifecycle. This is an engineering evidence grid,
not a claim about stochastic reliability or an autonomous allocation benefit.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from .common import save_json


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _unique_ticks(frames):
    """Prefer the later decision phase at a shared physical/decision boundary."""
    rows = {}
    for row in frames:
        rows[row['tick']] = row
    return [rows[key] for key in sorted(rows)]


def _old_frames(result):
    rows = {}
    for step in result['steps']:
        for frame in step['frames']:
            rows[round(frame['time']/.05)] = frame
    return [rows[key] for key in sorted(rows)]


def _idle_spans(rows, robot=0):
    spans, start = [], None
    for left, right in zip(rows[:-1], rows[1:]):
        idle = left['assignment'][robot]['target'] is None
        if idle and start is None:
            start = left['time']
        if not idle and start is not None:
            spans.append([start, left['time']])
            start = None
    if start is not None:
        spans.append([start, rows[-1]['time']])
    return spans


def _anchor_errors(case, rows, completion_times):
    """Derived error: measured robot positions versus frozen straight-line anchor.

    Only active assigned prefixes are plotted. Post-completion target motion is
    not misrepresented as an ongoing tracking-error observation.
    """
    output = []
    for target in case['targets']:
        j, q = target['id'], target['required_robots']
        angles = (-45., 45.) if q == 2 else (0., 120., 240.)
        offsets = [[.6*math.cos(math.radians(angle)), .6*math.sin(math.radians(angle))]
                   for angle in angles]
        values = []
        for row in rows:
            at = row['time']
            end = completion_times[j]
            if at < target['birth']-1e-10 or (end is not None and at > end+1e-10):
                continue
            members = [i for i, action in enumerate(row['assignment']) if action['target'] == j]
            # At the terminal endpoint real assignments have already been released.
            if end is not None and abs(at-end) <= 1e-10:
                members = list(range(q))
            if len(members) != q:
                continue
            center = [target['position_at_birth'][axis] + target['velocity'][axis]*(at-target['birth'])
                      for axis in (0, 1)]
            maximum = max(math.hypot(row['positions'][robot][0]-center[0]-offset[0],
                                     row['positions'][robot][1]-center[1]-offset[1])
                          for robot, offset in zip(members, offsets))
            values.append(dict(tick=row['tick'], time=at, max_anchor_error=maximum))
        output.append(dict(target=j, rows=values))
    return output


def plot_attempt(attempt, audit_path=None):
    """Create the requested 4 x 5 evidence figure after a successful raw audit.

    Matplotlib is imported only when this explicit function is called. English
    labels avoid dependence on unavailable CJK fonts. Root may supply audit_path
    when its output-directory naming differs from the standard acceptance job.
    """
    attempt = Path(attempt).resolve()
    if audit_path is None:
        candidates = sorted(attempt.rglob('scientific_audit.json'))
        if len(candidates) != 1:
            raise ValueError('Provide the unique saved scientific_audit.json explicitly')
        audit_path = candidates[0]
    else:
        audit_path = Path(audit_path).resolve()
    audit = _read(audit_path)
    if audit.get('passed') is not True:
        raise ValueError('Plotting acceptance summary requires the saved audit to have passed')
    design_path = attempt/'inputs/design.json'
    reference_path = attempt/'inputs/independent_reference.json'
    design, references = _read(design_path), _read(reference_path)
    cases = {row['case_id']: row for row in design['cases']}
    names = ['E1', 'E2', 'E3', 'E4', 'E5']
    if any(name not in cases or name not in audit['cases'] for name in names):
        raise ValueError('All five predeclared cases are required for this evidence figure')
    folder = attempt/'figures'
    folder.mkdir(parents=True, exist_ok=True)
    paths = {key: folder/name for key, name in dict(
        png='gq_execution_bridge.png', pdf='gq_execution_bridge.pdf',
        source='plot_source.json', alignment='panel_alignment.json').items()}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('Figure outputs already exist; preserve prior artifacts')
    source_paths = [design_path, reference_path, Path(audit_path)]
    data = {}
    for cid in names:
        result_path = attempt/'logs'/cid/'env/result.json'
        saved = _read(result_path)
        source_paths.append(result_path)
        rows = _unique_ticks(saved['snapshot']['frames'])
        if [row['tick'] for row in rows] != list(range(121)):
            raise ValueError('Missing physical endpoints in plotted execution: ' + cid)
        old = None
        if cid != 'E5':
            old_path = attempt/'logs'/(cid+'_old_G')/'env/result.json'
            old = _old_frames(_read(old_path))
            source_paths.append(old_path)
        data[cid] = dict(
            time=[r['time'] for r in rows], u0_x=[r['positions'][0][0] for r in rows],
            service_progress=[r['progress'] for r in rows],
            completion_times=saved['state']['completion_times'],
            anchor_errors=_anchor_errors(cases[cid], rows, saved['state']['completion_times']),
            quality_rows=audit['cases'][cid]['quality_rows'], idle_spans=_idle_spans(rows),
            old_G=None if old is None else dict(
                time=[r['time'] for r in old], u0_x=[r['positions'][0][0] for r in old],
                progress=[r['service_progress'][0] for r in old]),
            expected_old_G_completion=1.35,
            expected_A_completion=references[cid]['A_completion_time'],
            expected_B_completion=references[cid]['B_completion_time'])

    import matplotlib
    matplotlib.use('Agg', force=True)
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import numpy as np

    measured, task_b, old_color = '#176D9C', '#14805E', '#777777'
    expected_color, fault_color = '#795098', '#E7C8A3'
    descriptions = ['Normal pair', 'Larger declared sigma', 'Missing U1 measurement',
                    'Triad, missing U2', 'Release then scripted reuse']
    settings = {'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 11,
                'axes.labelsize': 10, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
                'pdf.fonttype': 42, 'ps.fonttype': 42, 'axes.spines.top': False,
                'axes.spines.right': False, 'axes.linewidth': .7,
                'xtick.direction': 'out', 'ytick.direction': 'out'}
    with plt.rc_context(settings):
        fig, axes = plt.subplots(4, 5, figsize=(20, 12), sharex=True, sharey='row')
        fig.subplots_adjust(left=.065, right=.99, bottom=.17, top=.895, wspace=.17, hspace=.30)
        fig.suptitle('Controlled GQ execution: geometry, public quality, service, and physical reuse',
                     x=.065, y=.974, ha='left', fontsize=16, fontweight='bold')
        fig.text(.065, .943,
                 'Solid curves: measured execution / saved sensing audit. Dashed vertical lines: analytic expectations.',
                 ha='left', fontsize=10, color='#444444')
        all_x = [x for row in data.values() for x in row['u0_x']]
        all_radius = [r['radius_proxy'] for row in data.values() for r in row['quality_rows']
                      if r['radius_proxy'] is not None]
        radius_top = max(.14, max(all_radius, default=0.)*1.12)
        for col, cid in enumerate(names):
            case, row = cases[cid], data[cid]
            times = row['time']
            axes[0, col].set_title(chr(ord('a')+col) + '  ' + cid + ' | ' + descriptions[col], loc='left', pad=11)
            for r in range(4):
                ax = axes[r, col]
                ax.set_xlim(0, 6)
                ax.set_xticks([0, 1, 2, 3, 4, 5, 6])
                ax.grid(axis='y', color='#D9DEE3', linewidth=.55, alpha=.8)
                ax.set_axisbelow(True)
                if r:
                    ax.text(0., 1.055, chr(ord('a')+r*5+col), transform=ax.transAxes,
                            fontsize=10, fontweight='bold')
                if case['disturbance']['mode'] != 'normal':
                    ax.axvspan(.75, 1.25, color=fault_color, alpha=.35, linewidth=0, zorder=0)
                ax.axvline(row['expected_old_G_completion'], color=old_color,
                           linestyle=(0, (4, 3)), linewidth=.9, alpha=.8)
                if abs(row['expected_A_completion']-row['expected_old_G_completion']) > 1e-10:
                    ax.axvline(row['expected_A_completion'], color=expected_color,
                               linestyle=(0, (2, 2)), linewidth=1.)
                if cid == 'E5':
                    ax.axvline(3., color=task_b, linestyle=(0, (5, 2, 1, 2)), linewidth=.9)
                    ax.axvline(row['expected_B_completion'], color=expected_color,
                               linestyle=(0, (2, 2)), linewidth=1.)
            for task in row['anchor_errors']:
                points = task['rows']
                axes[0, col].plot([r['time'] for r in points], [r['max_anchor_error'] for r in points],
                                  color=measured if task['target'] == 0 else task_b, linewidth=1.65)
            axes[0, col].axhline(.15, color='#A34638', linewidth=1., linestyle=':')
            axes[0, col].set_ylim(-.008, .225)

            for target in case['targets']:
                points = [r for r in row['quality_rows'] if r['target'] == target['id']]
                xx = [r['time'] for r in points]
                yy = [float('nan') if r['radius_proxy'] is None else r['radius_proxy'] for r in points]
                axes[1, col].plot(xx, yy, color=measured if target['id'] == 0 else task_b, linewidth=1.65)
                missing = [r['time'] for r in points if r['radius_proxy'] is None]
                if missing:
                    axes[1, col].plot(missing, [.9]*len(missing), transform=axes[1, col].get_xaxis_transform(),
                                      linestyle='none', marker='x', markersize=4, color='#333333')
            axes[1, col].axhline(.06, color='#A34638', linewidth=1., linestyle=':')
            axes[1, col].set_ylim(-.005, radius_top)

            if row['old_G'] is not None:
                axes[2, col].plot(row['old_G']['time'], row['old_G']['progress'],
                                  color=old_color, linestyle='--', linewidth=2.0, alpha=.75)
            axes[2, col].plot(times, [p[0] for p in row['service_progress']], color=measured, linewidth=1.65)
            axes[2, col].axhline(1.05, color='#777777', linestyle=':', linewidth=.7)
            if cid == 'E5':
                selected = [i for i, t in enumerate(times) if t >= 3.]
                axes[2, col].plot([times[i] for i in selected],
                                  [row['service_progress'][i][1] for i in selected], color=task_b, linewidth=1.65)
            axes[2, col].set_ylim(-.04, 1.18)

            for lo, hi in row['idle_spans']:
                axes[3, col].axvspan(lo, hi, color='#DCE7ED', alpha=.60, linewidth=0, zorder=0)
            if row['old_G'] is not None:
                axes[3, col].plot(row['old_G']['time'], row['old_G']['u0_x'],
                                  color=old_color, linestyle='--', linewidth=2.0, alpha=.75)
            axes[3, col].plot(times, row['u0_x'], color=measured, linewidth=1.65)
            axes[3, col].set_ylim(min(all_x)-.08, max(all_x)+.08)
            axes[3, col].set_xlabel('Simulation time (s)')
            if cid == 'E5':
                axes[3, col].annotate('actual idle', xy=(2.65, row['u0_x'][46]),
                                      xytext=(2.52, min(all_x)+.12), fontsize=8,
                                      arrowprops=dict(arrowstyle='-', color='#555555', linewidth=.7))
        for r, label in enumerate(('Max role-anchor error\n(active task only)',
                                   'Local radius proxy\n(not actual WLS error)',
                                   'Service progress (s)', 'Measured U0 x position')):
            axes[r, 0].set_ylabel(label)
        legend = [Line2D([], [], color=measured, lw=1.8, label='GQ / task A: measured'),
                  Line2D([], [], color=task_b, lw=1.8, label='Task B: measured'),
                  Line2D([], [], color=old_color, lw=1.8, ls='--', label='Old G: measured control'),
                  Line2D([], [], color=old_color, lw=1., ls='--', label='Expected (analytic): old G stop 1.35 s'),
                  Line2D([], [], color=expected_color, lw=1., ls=':', label='Expected (analytic): GQ completion'),
                  Line2D([], [], color='#A34638', lw=1., ls=':', label='Declared geometry / quality thresholds'),
                  Patch(facecolor=fault_color, alpha=.35, label='Declared intervention [0.75, 1.25)'),
                  Patch(facecolor='#DCE7ED', alpha=.60, label='U0 actually IDLE'),
                  Line2D([], [], color='#333333', marker='x', ls='none', label='Q unavailable: no numeric radius')]
        fig.legend(handles=legend, loc='lower left', bbox_to_anchor=(.061, .069), ncol=3,
                   frameon=False, fontsize=9, handlelength=2.8, columnspacing=2.5)
        fig.text(.065, .040,
                 'Anchor errors use measured robot positions and the frozen straight-line target input. '
                 'Q curves use saved estimated-state information; UNKNOWN remains missing.', fontsize=9)
        fig.text(.065, .020,
                 'One deterministic episode per case. These figures do not establish stochastic accuracy, '
                 'real-time throughput, autonomous allocation, or a GQ M3 certificate.', fontsize=9)
        fig.canvas.draw()
        rectangles = []
        for r in range(4):
            for c in range(5):
                box = axes[r, c].get_position()
                rectangles.append(dict(row=r, col=c, x_pt=float(box.x0*20*72), y_pt=float(box.y0*12*72),
                                       width_pt=float(box.width*20*72), height_pt=float(box.height*12*72)))
        widths = [r['width_pt'] for r in rectangles]
        heights = [r['height_pt'] for r in rectangles]
        if max(widths)-min(widths) > 1.5 or max(heights)-min(heights) > 1.5:
            raise AssertionError('Equal-grid plot areas are not aligned within 1.5 pt')
        fig.savefig(paths['png'], dpi=180, facecolor='white')
        fig.savefig(paths['pdf'], facecolor='white', metadata=dict(Title='GQ execution bridge: deterministic mechanism evidence'))
        plt.close(fig)
    sources = {str(p.relative_to(attempt)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    save_json(paths['source'], dict(cases=data, source_sha256=sources,
                                  statement='Only saved outputs are plotted; anchor error is a documented derived quantity.'))
    save_json(paths['alignment'], dict(passed=True, tolerance_pt=1.5, axes=rectangles,
                                      width_spread_pt=max(widths)-min(widths), height_spread_pt=max(heights)-min(heights),
                                      note='Measured final equal-grid plot rectangles; separate visual/PDF text review is still required.'))
    return dict(passed=True, files={key: str(path) for key, path in paths.items()},
                cases=names, layout='4 rows x 5 cases', audit_source=str(audit_path),
                scope='measured deterministic engineering results; analytic lines explicitly labeled',
                visual_review_pending=True)
