import { useState } from 'react';
import { uploadFiles } from '../api';

const FileUpload = ({ onSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [lastMeta, setLastMeta] = useState(null);
  const [error, setError] = useState('');

  const handleChange = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError('');
    try {
      const res = await uploadFiles(files);
      setLastMeta({
        columns: res.columns || [],
        shape: res.df_shape || [0, 0],
      });
      onSuccess?.(res);
    } catch (err) {
      console.error(err);
      setError('上传失败：请确认后端已启动，且文件格式为 CSV/Excel。');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="upload-box">
      <h2>上传 Excel / CSV</h2>
      <p>支持多文件；Pureclaw 会自动清洗并生成可分析的数据预览。</p>

      <label className="upload-label" role="button" tabIndex={0}>
        <input
          type="file"
          multiple
          accept=".xlsx,.xls,.csv"
          onChange={handleChange}
          disabled={uploading}
        />
        <span>{uploading ? '上传中…' : '选择文件并上传'}</span>
      </label>

      {error && <div className="current-query">{error}</div>}

      {lastMeta && (
        <div className="current-query">
          已加载：{lastMeta.shape?.[0]} 行 · {lastMeta.shape?.[1]} 列（{lastMeta.columns.length} 列名）
        </div>
      )}
    </div>
  );
};

export default FileUpload;
