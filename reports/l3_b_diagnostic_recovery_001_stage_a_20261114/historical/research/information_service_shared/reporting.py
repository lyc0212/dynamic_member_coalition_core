"""Report only phases for which saved execution records exist."""
from pathlib import Path
from .common import read_json,save_json,sha_file


def report(attempt):
    attempt=Path(attempt)
    result_file=attempt/'result.json'
    if not result_file.exists():
        status='PREPARED_NOT_RUN'
        result=dict(passed=False,status=status,scientific_execution_started=False)
        text='共享实现与运行材料已准备；尚未运行准入、检查或科学实验。'
    else:
        result=read_json(result_file);status=result['status']
        if result.get('passed') is True:
            text='保存结果报告确定性等价验收通过；CPU仅作诊断，不构成稳定加速声明。'
        else:
            text='运行已停止并保留证据。未完成的阶段不能计为通过。错误：'+result.get('error','见失败记录')
    target=attempt/'REPORT.md'
    target.write_text('# GQ批内共享状态\n\n'+text+'\n\n状态：`'+status+'`。\n',encoding='utf-8')
    receipt=dict(status=status,path=str(target),sha256=sha_file(target),source_result=str(result_file) if result_file.exists() else None)
    save_json(attempt/'report_receipt.json',receipt);return receipt
