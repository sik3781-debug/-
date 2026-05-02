function addCoverSlide(pres, title, date) {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:0.06, fill:{ color:'000080' }, line:{ color:'000080' } });
  s.addText([
    { text:'중기이코노미기업지원단', options:{ bold:true } },
    { text:'   |   기업 맞춤형 컨설팅 솔루션', options:{ bold:false } }
  ], { x:0.55, y:0.28, w:9, h:0.32, fontSize:11, color:'000080', fontFace:'나눔고딕' });
  s.addText(title, { x:0.55, y:1.65, w:8.9, h:0.85, fontSize:30, bold:true, color:'000080', fontFace:'나눔고딕', align:'left' });
  s.addShape(pres.shapes.LINE, { x:0.55, y:2.68, w:2.4, h:0, line:{ color:'000080', width:1.5 } });
  s.addText(date, { x:0.55, y:5.10, w:3, h:0.28, fontSize:9.5, color:'94A3B8', fontFace:'Calibri', align:'left' });
  s.addText('영남사업단 경남1본부(진주센터)  전문위원 여운식  010-2673-3781', { x:3.8, y:5.10, w:6.05, h:0.28, fontSize:9, color:'334155', fontFace:'나눔고딕', align:'right' });
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:5.55, w:10, h:0.075, fill:{ color:'D1D9E6' }, line:{ color:'D1D9E6' } });
}
function addEndingSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:0.06, fill:{ color:'000080' }, line:{ color:'000080' } });
  s.addText([
    { text:'중기이코노미기업지원단', options:{ bold:true } },
    { text:'   |   기업 맞춤형 컨설팅 솔루션', options:{ bold:false } }
  ], { x:0.55, y:0.28, w:9, h:0.32, fontSize:11, color:'000080', fontFace:'나눔고딕' });
  s.addText('감사합니다', { x:0, y:1.75, w:10, h:1.0, fontSize:46, bold:true, color:'000080', fontFace:'나눔고딕', align:'center' });
  s.addShape(pres.shapes.LINE, { x:4.3, y:3.02, w:1.4, h:0, line:{ color:'000080', width:1.2 } });
  s.addText([
    { text:'중기이코노미기업지원단  영남사업단 경남1본부(진주센터)', options:{ breakLine:true } },
    { text:'전문위원 여운식  |  010-2673-3781' }
  ], { x:0, y:3.2, w:10, h:0.65, fontSize:11, color:'334155', fontFace:'나눔고딕', align:'center' });
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:5.55, w:10, h:0.075, fill:{ color:'D1D9E6' }, line:{ color:'D1D9E6' } });
}

