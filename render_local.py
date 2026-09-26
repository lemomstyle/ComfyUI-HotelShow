"""Offline renderer for approved JSON plans; no model call and no API key needed."""
import argparse
import json
from pathlib import Path
from engine import read_source, parse_plan, render, contact_sheets, make_prompt

if __name__ == '__main__':
    p=argparse.ArgumentParser(description='HotelShow：从已审核策划 JSON 生成图文长图')
    p.add_argument('--input',required=True,help='图片 ZIP 或单张图片')
    p.add_argument('--hotel',required=True)
    p.add_argument('--plan',help='模型返回的 JSON 文件；不填时仅生成联系表与策划提示词')
    p.add_argument('--output',required=True)
    p.add_argument('--width',type=int,default=1080)
    p.add_argument('--height',type=int,default=1440)
    args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    photos,warnings=read_source(args.input)
    for i,im in enumerate(contact_sheets(photos),1):im.save(out/f'contact_{i:02}.jpg',quality=92)
    (out/'planning_prompt.txt').write_text(make_prompt(photos,args.hotel,'','自动选择'),encoding='utf-8')
    if args.plan:
        plan=parse_plan(Path(args.plan).read_text(encoding='utf-8'),photos)
        pages,long,report=render(photos,plan,args.hotel,args.width,args.height)
        for i,im in enumerate(pages,1):im.save(out/f'page_{i:02}.png')
        long.save(out/'long.png')
        report['input_warnings']=warnings
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'完成：{len(pages)} 页；{long.width} × {long.height} 长图。')
    else:
        print('已生成联系表和 planning_prompt.txt。把它们交给多模态模型，再用 --plan 导入结果。')
