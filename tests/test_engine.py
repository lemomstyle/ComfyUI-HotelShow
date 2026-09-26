import copy
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine as e


def photo(i,size=(900,600),color='#998877'):
    return {'id':f'P{i:03}','name':f'{i}.png','image':e.Image.new('RGB',size,color)}


def plan(photos):
    ids=[p['id'] for p in photos]
    return {'version':1,'theme':'ivory','font_style':'sans','title':'慢下来，住进好时光',
            'subtitle':'排版测试 · 非酒店实拍','cover_id':ids[0],
            'images':[{'id':i,'scene':'测试','visible':'测试色块'} for i in ids],
            'sections':[{'title':'日常的温度','kicker':'THE STAY','body':'这是用于验证中文换行和图片比例的测试内容。',
                         'photo_ids':ids[x:x+4],'layout':'auto'} for x in range(0,len(ids),4)],
            'excluded':[],'review_notes':[]}


class EngineTests(unittest.TestCase):
    def test_valid_plan_and_fenced_json(self):
        photos=[photo(1)]
        self.assertEqual(e.parse_plan('```json\n'+json.dumps(plan(photos))+'\n```',photos)['cover_id'],'P001')
    def test_refuse_unknown_id(self):
        photos=[photo(1)];p=plan(photos);p['sections'][0]['photo_ids']=['P099']
        with self.assertRaises(ValueError):e.parse_plan(json.dumps(p),photos)
    def test_refuse_omitted_photo(self):
        photos=[photo(1),photo(2)];p=plan(photos);p['sections'][0]['photo_ids']=['P001']
        with self.assertRaises(ValueError):e.parse_plan(json.dumps(p),photos)
    def test_excluded_photo_requires_reason(self):
        photos=[photo(1),photo(2)];p=plan(photos);p['sections'][0]['photo_ids']=['P001'];p['excluded']=[{'id':'P002'}]
        with self.assertRaises(ValueError):e.parse_plan(json.dumps(p),photos)
    def test_complete_exclusion_is_accepted(self):
        photos=[photo(1),photo(2)];p=plan(photos);p['sections'][0]['photo_ids']=['P001'];p['excluded']=[{'id':'P002','reason':'测试'}]
        self.assertEqual(e.parse_plan(json.dumps(p),photos)['excluded'][0]['id'],'P002')
    def test_excluded_cover_rejected(self):
        photos=[photo(1),photo(2)];p=plan(photos);p['sections'][0]['photo_ids']=['P002'];p['excluded']=[{'id':'P001','reason':'测试'}]
        with self.assertRaises(ValueError):e.parse_plan(json.dumps(p),photos)
    def test_incomplete_analysis_rejected(self):
        photos=[photo(1),photo(2)];p=plan(photos);p['images']=p['images'][:1]
        with self.assertRaises(ValueError):e.parse_plan(json.dumps(p),photos)
    def test_api_error_is_not_rendered_as_copy(self):
        with self.assertRaises(ValueError):e.parse_plan('[ERROR] HTTP 401',[photo(1)])
    def test_overflow_rejected(self):
        im=e.Image.new('RGB',(640,1000));d=e.ImageDraw.Draw(im)
        with self.assertRaises(ValueError):e.text_box(d,'文案'*200,(0,0,100,60),30,'black')
    def test_wrap_stays_within_width(self):
        f=e.font(28)
        lines=e.wrap('窗外是街景，房间里留出一段属于自己的时间。'*3,f,220)
        self.assertTrue(all(f.getlength(line)<=220 for line in lines))
    def test_contain_keeps_entire_photo(self):
        src=e.Image.new('RGB',(400,100),'red');d=e.ImageDraw.Draw(src);d.rectangle((0,0,399,99),outline='blue',width=8)
        dst=e.contain(src,(200,200),'white')
        self.assertEqual(dst.getpixel((100,20)),(255,255,255))
        self.assertEqual(dst.getpixel((0,75)),(0,0,255))
        self.assertEqual(dst.getpixel((199,124)),(0,0,255))
    def test_mixed_aspects_and_all_themes(self):
        photos=[photo(1,(1600,900)),photo(2,(600,900)),photo(3,(800,800)),photo(4,(2000,500))]
        for theme in e.THEMES:
            p=plan(photos);p['theme']=theme
            pages,long,report=e.render(photos,p,'排版测试酒店',750,1200)
            self.assertEqual(long.size,(750,2400));self.assertEqual(len(pages),2)
            for x,y,w,h in report['layout'][1]['photo_boxes']:
                self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                self.assertLessEqual(x+w,750);self.assertLessEqual(y+h,1200)
    def test_24_photos_are_represented(self):
        photos=[photo(i,(600,400)) for i in range(1,25)]
        p=e.parse_plan(json.dumps(plan(photos)),photos)
        self.assertEqual(len(e.contact_sheets(photos)),4)
        pages,long,report=e.render(photos,p,'素材覆盖测试',640,1000)
        used=[i for a in report['layout'][1:] for i in a['photo_ids']]
        self.assertEqual(set(used),{p['id'] for p in photos});self.assertEqual(len(pages),7)
    def test_zip_natural_order_duplicate_and_no_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            zpath=Path(td)/'in.zip'
            a=io.BytesIO();b=io.BytesIO()
            e.Image.new('RGB',(100,100),'red').save(a,format='PNG')
            e.Image.new('RGB',(200,100),'green').save(b,format='PNG')
            with zipfile.ZipFile(zpath,'w') as z:
                z.writestr('room10.png',b.getvalue());z.writestr('room2.png',a.getvalue())
                z.writestr('room20.png',a.getvalue());z.writestr('__MACOSX/junk.png',b'junk')
                z.writestr('../../outside.txt','untrusted')
            photos,warnings=e.read_source(zpath)
            self.assertEqual([p['name'] for p in photos],['room2.png','room10.png'])
            self.assertEqual(len(warnings),1);self.assertEqual(len(list(Path(td).iterdir())),1)
    def test_bad_zip_image_fails_clearly(self):
        with tempfile.TemporaryDirectory() as td:
            zpath=Path(td)/'in.zip'
            with zipfile.ZipFile(zpath,'w') as z:z.writestr('broken.png',b'bad')
            with self.assertRaisesRegex(ValueError,'broken.png'):e.read_source(zpath)
    def test_too_many_input_files_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            zpath=Path(td)/'in.zip'
            with zipfile.ZipFile(zpath,'w') as z:
                for i in range(25):z.writestr(f'{i}.png',b'fake')
            with self.assertRaisesRegex(ValueError,'24'):e.read_source(zpath)


if __name__=='__main__':unittest.main(verbosity=2)
