import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';

app.registerExtension({
  name: 'HotelShow.Upload',
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== 'HotelShowPrepare') return;
    const original = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      original?.apply(this, arguments);
      const node = this;
      this.addWidget('button', '上传 ZIP / 选择多张图片', null, () => {
        const picker = document.createElement('input');
        picker.type = 'file';
        picker.multiple = true;
        picker.accept = '.zip,.png,.jpg,.jpeg,.webp';
        picker.onchange = async () => {
          if (!picker.files?.length) return;
          const body = new FormData();
          for (const f of picker.files) body.append('file', f);
          try {
            const response = await api.fetchApi('/hotelshow/upload', { method: 'POST', body });
            if (!response.ok) throw new Error(await response.text());
            const result = await response.json();
            const source = node.widgets.find(w => w.name === 'source');
            source.value = result.source;
            source.callback?.(source.value);
            node.setDirtyCanvas(true, true);
          } catch (e) {
            alert('上传失败：' + e.message + '\n若 RunningHub 不支持此扩展，请使用多图连线版。');
          }
        };
        picker.click();
      }, { serialize: false });
    };
  }
});
