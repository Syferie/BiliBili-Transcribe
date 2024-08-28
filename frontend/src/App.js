import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  TextField, Button, Paper, Typography, Box, CircularProgress, 
  Container, AppBar, Toolbar, IconButton, Snackbar, Fade, Grow,
  Card, CardContent, Divider, Chip, useMediaQuery, 
  List, ListItem, ListItemText, Dialog, DialogTitle, DialogContent,
  DialogActions, Alert, Select, MenuItem, FormControl, InputLabel,
  Pagination, Checkbox, ListItemIcon, ListItemButton, ListItemSecondaryAction,
  FormHelperText // 添加这一行
} from '@mui/material';
import { createTheme, ThemeProvider, useTheme } from '@mui/material/styles';
import { 
  Menu as MenuIcon, 
  Subtitles as SubtitlesIcon, 
  Close as CloseIcon,
  YouTube as YouTubeIcon,
  ContentCopy as ContentCopyIcon,
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  History as HistoryIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import BilibiliIcon from './assets/bilibili-icon.svg';  // 新增的 Bilibili 图标导入
const colors = [
  '#FFD1DC', '#BFFFBF', '#BFEFFF', '#FFFFBF', '#FFE5BF', 
  '#E6BFFF', '#FFBFEF', '#BFE6FF', '#DFFFBF', '#FFDFBF'
];

const TranscriptSentence = ({ sentence, index }) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(sentence.text);
  };

  const formatTimestamp = (start, end) => {
    const formatTime = (time) => {
      const minutes = Math.floor(time / 60);
      const seconds = Math.floor(time % 60);
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };
    return `${formatTime(start)} - ${formatTime(end)}`;
  };

  return (
    <Box
      sx={{
        marginBottom: 2,
        position: 'relative',
      }}
    >
      <Typography
        variant="caption"
        sx={{
          position: 'absolute',
          top: -15,
          left: 0,
          color: 'text.secondary',
          fontSize: '0.7rem',
        }}
      >
        {formatTimestamp(sentence.start, sentence.end)}
      </Typography>
      <Box
        component="span"
        sx={{
          backgroundColor: colors[index % colors.length],
          color: '#333',
          padding: '2px 6px',
          margin: '0 3px',
          borderRadius: '4px',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          display: 'inline-block',
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          },
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handleCopy}
      >
        {sentence.text}
      </Box>
    </Box>
  );
};

function App() {
  const [mode, setMode] = useState('light');
  const [transcriberType, setTranscriberType] = useState('');
  const [exportingSrt, setExportingSrt] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingEntry, setEditingEntry] = useState(null);
  const [selectedEntries, setSelectedEntries] = useState([]);
  const [sortBy, setSortBy] = useState('date'); // 新增：排序选项
  const itemsPerPage = 10;

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: mode === 'light' ? '#1976d2' : '#90caf9',
          },
          secondary: {
            main: mode === 'light' ? '#dc004e' : '#f48fb1',
          },
          background: {
            default: mode === 'light' ? '#f5f5f5' : '#303030',
            paper: mode === 'light' ? '#ffffff' : '#424242',
          },
        },
        typography: {
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      }),
    [mode],
  );

  const [bvId, setBvId] = useState('');
  const [transcript, setTranscript] = useState('');
  const [videoTitle, setVideoTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState([]);
  const [openHistory, setOpenHistory] = useState(false);
  const [status, setStatus] = useState('');

  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(20);
  const startTimeRef = useRef(null);
  const progressIntervalRef = useRef(null);

  const handleHistoryItemClick = (item) => {
    setBvId(item.bvId);
    setVideoTitle(item.title);
    setTranscript(item.transcript);
    setTranscriberType(item.transcriberType);
    setOpenHistory(false);
  };

  const handleCheckboxChange = (e, id) => {
    e.stopPropagation();
    setSelectedEntries(
      e.target.checked
        ? [...selectedEntries, id]
        : selectedEntries.filter(entryId => entryId !== id)
    );
  };
  
  const handleExportSrt = async () => {
    setExportingSrt(true);
    try {
      const response = await fetch('/api/export_srt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transcript, videoTitle }),
      });

      if (!response.ok) {
        throw new Error('导出 SRT 失败');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${videoTitle}.srt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError(error.message);
    } finally {
      setExportingSrt(false);
    }
  };

  useEffect(() => {
    const savedHistory = JSON.parse(localStorage.getItem('transcriptionHistory')) || [];
    // 确保 savedHistory 是一个数组，并且每个项都有正确的结构
    const validHistory = Array.isArray(savedHistory) ? savedHistory.filter(item => 
      item && typeof item === 'object' && 'bvId' in item && 'title' in item
    ) : [];
    setHistory(validHistory);
  }, []);


  const [enabledTranscribers, setEnabledTranscribers] = useState({});
  
  useEffect(() => {
    fetch('/api/enabled_transcribers')
      .then(response => response.json())
      .then(data => {
        setEnabledTranscribers(data);
        // 设置默认的转写服务
        const firstEnabledTranscriber = Object.keys(data).find(key => data[key]);
        if (firstEnabledTranscriber) {
          setTranscriberType(firstEnabledTranscriber);
        }
      })
      .catch(error => {
        console.error('Error fetching enabled transcribers:', error);
        setError('无法获取可用的转写服务');
      });
  }, []);

  // 在 Select 组件中添加错误处理和禁用逻辑
  const noEnabledTranscribers = Object.values(enabledTranscribers).every(value => !value);
  
  const saveHistory = (newHistory) => {
    localStorage.setItem('transcriptionHistory', JSON.stringify(newHistory));
    setHistory(newHistory);
  };

  const addToHistory = (entry) => {
    const newHistory = [entry, ...history];
    saveHistory(newHistory);
  };

  const deleteEntry = (id) => {
    const newHistory = history.filter(item => item.id !== id);
    saveHistory(newHistory);
  };

  const updateEntry = (updatedEntry) => {
    const newHistory = history.map(item => 
      item.id === updatedEntry.id ? updatedEntry : item
    );
    saveHistory(newHistory);
  };

  const calculateEstimatedTime = (duration) => {
    const estimatedSeconds = (duration / 180) * 25;
    return Math.max(20, estimatedSeconds);
  };
  
  const startProgressEstimation = () => {
    startTimeRef.current = Date.now();
    setProgress(0);
    progressIntervalRef.current = setInterval(() => {
      const elapsedTime = (Date.now() - startTimeRef.current) / 1000;
      const newProgress = Math.min((elapsedTime / estimatedTime) * 100, 99);
      setProgress(newProgress);
    }, 100);
  };

  const stopProgressEstimation = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
  };

  // 修改 handleSubmit 函数
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setTranscript('');
    setVideoTitle('');
    setStatus('开始处理');
    startProgressEstimation();

    try {
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ bvId, transcriber_type: transcriberType }),
      });

      if (!response.ok) {
        throw new Error('转写请求失败');
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      console.log("Received data:", data);

      const calculatedEstimatedTime = calculateEstimatedTime(data.duration);
      setEstimatedTime(calculatedEstimatedTime);

      // 确保 transcript 是一个数组，每个元素包含 text, start, 和 end
      const formattedTranscript = Array.isArray(data.transcript) ? data.transcript : [{
        text: data.transcript,
        start: 0,
        end: data.duration || 0
      }];
      setTranscript(formattedTranscript);

      setVideoTitle(data.title);
      setShowSnackbar(true);
      
      // 添加到历史记录
      const newEntry = {
        id: Date.now(),
        bvId,
        title: data.title,
        transcriberType,
        createdAt: new Date().toISOString(),
        tags: [],
        transcript: formattedTranscript  // 保存完整的转录内容
      };
      addToHistory(newEntry);

      pollProgress(bvId);
    } catch (err) {
      setError(err.message || '发生未知错误');
      stopProgressEstimation();
    } finally {
      setLoading(false);
    }
  };

  const [selectedHistoryEntry, setSelectedHistoryEntry] = useState(null);

  const pollProgress = async (bvId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/progress?bvId=${bvId}`);
        const data = await response.json();
        setStatus(data.status);
        if (data.status === '处理完成' || data.status === '转写失败') {
          clearInterval(pollInterval);
          stopProgressEstimation();
          if (data.status === '转写失败') {
            setError(data.details || '转写过程中发生错误');
          } else {
            setProgress(100);
          }
        }
      } catch (error) {
        console.error('Error polling progress:', error);
      }
    }, 1000);
  };

  const handleCopyTranscript = () => {
    const textToCopy = Array.isArray(transcript) 
      ? transcript.map(t => t.text).join(' ')
      : transcript;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const countChineseCharacters = (text) => {
    if (Array.isArray(text)) {
      text = text.map(t => t.text).join('');
    }
    return (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  };

  // 修改 filteredHistory 的实现
  const filteredHistory = useMemo(() => {
    return history.filter(item =>
      (item?.title?.toLowerCase() ?? '').includes(searchTerm.toLowerCase()) ||
      (item?.bvId?.toLowerCase() ?? '').includes(searchTerm.toLowerCase())
    );
  }, [history, searchTerm]);

  const sortedHistory = [...filteredHistory].sort((a, b) => {
    if (sortBy === 'date') {
      return new Date(b.createdAt) - new Date(a.createdAt);
    } else if (sortBy === 'title') {
      return a.title.localeCompare(b.title);
    }
    return 0;
  });

  const paginatedHistory = sortedHistory.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(sortedHistory.length / itemsPerPage);

  const handlePageChange = (event, value) => {
    setCurrentPage(value);
  };

  const handleDeleteEntry = (id) => {
    deleteEntry(id);
  };

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
  };

  const handleUpdateTags = () => {
    if (editingEntry) {
      updateEntry(editingEntry);
      setEditingEntry(null);
    }
  };

  const handleBulkDelete = () => {
    const newHistory = history.filter(item => !selectedEntries.includes(item.id));
    saveHistory(newHistory);
    setSelectedEntries([]);
  };

  const handleExport = () => {
    const dataToExport = selectedEntries.length > 0
      ? history.filter(item => selectedEntries.includes(item.id))
      : history;
    
    const jsonString = JSON.stringify(dataToExport, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transcription_history.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: 'background.default' }}>
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <IconButton
              size="large"
              edge="start"
              color="inherit"
              aria-label="menu"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              哔哩哔哩视频转写工具
            </Typography>
            <IconButton color="inherit" onClick={() => setOpenHistory(true)}>
              <HistoryIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}>
              {mode === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
            </IconButton>
          </Toolbar>
        </AppBar>
        <Container maxWidth="md">
          <Box sx={{ my: 4 }}>
            <Grow in={true} timeout={1000}>
              <Card elevation={3}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <img src={BilibiliIcon} alt="Bilibili" style={{ width: 24, height: 24, marginRight: 8 }} />
                    <Typography variant="h5" component="div">
                      视频转写
                    </Typography>
                  </Box>
                  <Divider sx={{ mb: 3 }} />
                  <form onSubmit={handleSubmit}>
                    <TextField
                      label="输入BV号"
                      variant="outlined"
                      value={bvId}
                      onChange={(e) => setBvId(e.target.value)}
                      required
                      fullWidth
                      margin="normal"
                      InputProps={{
                        startAdornment: <SubtitlesIcon color="action" sx={{ mr: 1 }} />,
                      }}
                    />
                    <FormControl fullWidth margin="normal" error={noEnabledTranscribers}>
                      <InputLabel id="transcriber-type-label">转写服务</InputLabel>
                      <Select
                        labelId="transcriber-type-label"
                        value={transcriberType}
                        onChange={(e) => setTranscriberType(e.target.value)}
                        label="转写服务"
                        disabled={noEnabledTranscribers}
                      >
                        {enabledTranscribers.faster_whisper && (
                          <MenuItem value="faster_whisper">本地 Faster Whisper</MenuItem>
                        )}
                        {enabledTranscribers.openai && (
                          <MenuItem value="openai">OpenAI Whisper</MenuItem>
                        )}
                        {enabledTranscribers.cloud_faster_whisper && (
                          <MenuItem value="cloud_faster_whisper">云端 Faster Whisper</MenuItem>
                        )}
                      </Select>
                      {noEnabledTranscribers && (
                        <FormHelperText>没有可用的转写服务</FormHelperText>
                      )}
                    </FormControl>
                    <Button 
                      type="submit" 
                      variant="contained" 
                      color="primary"
                      disabled={loading}
                      fullWidth
                      size="large"
                      sx={{ mt: 2 }}
                    >
                      {loading ? <CircularProgress size={24} /> : '获取字幕'}
                    </Button>
                  </form>
                  {loading && (
                    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgress
                        variant="determinate"
                        value={progress}
                        size={60}
                        thickness={4}
                      />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {status}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {progress.toFixed(0)}%
                      </Typography>
                    </Box>
                  )}
                  {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {error.includes('Cloud Faster Whisper') ? '云端 Faster Whisper 服务出错，请稍后重试' : error}
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grow>
            {transcript && Array.isArray(transcript) && (
              <Fade in={Boolean(transcript)} timeout={500}>
                <Card elevation={3} sx={{ mt: 4, position: 'relative' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      视频标题: {videoTitle}
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                      转写结果:
                    </Typography>
                    <Paper 
                      elevation={0} 
                      sx={{ 
                        p: 2, 
                        maxHeight: 300, 
                        overflow: 'auto', 
                        backgroundColor: theme.palette.mode === 'light' ? '#f8f8f8' : '#333',
                        borderRadius: 2,
                        lineHeight: 1.6,
                      }}
                    >
                      {transcript.map((sentence, index) => (
                        <TranscriptSentence key={index} sentence={sentence} index={index} />
                      ))}
                    </Paper>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
                      <Button
                        variant="outlined"
                        startIcon={<ContentCopyIcon />}
                        onClick={handleCopyTranscript}
                      >
                        {copied ? '已复制' : '复制全部文本'}
                      </Button>
                      <Button
                        variant="contained"
                        startIcon={exportingSrt ? <CircularProgress size={20} /> : <FileDownloadIcon />}
                        onClick={handleExportSrt}
                        disabled={exportingSrt}
                      >
                        {exportingSrt ? '导出中...' : '导出 SRT'}
                      </Button>
                    </Box>
                  </CardContent>
                  <Chip
                    label={`共 ${countChineseCharacters(transcript)} 个字`}
                    color="primary"
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 16,
                      right: 16,
                    }}
                  />
                </Card>
              </Fade>
            )}
          </Box>
        </Container>
        <Snackbar
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'center',
          }}
          open={showSnackbar}
          autoHideDuration={3000}
          onClose={() => setShowSnackbar(false)}
          message="转写完成！"
          action={
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={() => setShowSnackbar(false)}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        />
        <Dialog open={openHistory} onClose={() => setOpenHistory(false)} fullWidth maxWidth="md">
          <DialogTitle>
            历史记录
            <TextField
              variant="outlined"
              size="small"
              placeholder="搜索..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ marginLeft: 16 }}
            />
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              size="small"
              style={{ marginLeft: 16 }}
            >
              <MenuItem value="date">按日期排序</MenuItem>
              <MenuItem value="title">按标题排序</MenuItem>
            </Select>
          </DialogTitle>
          <DialogContent>
            <List>
              {paginatedHistory.map((item) => (
                <ListItem
                  key={item.id}
                  disablePadding
                >
                  <ListItemButton onClick={() => handleHistoryItemClick(item)}>
                    <ListItemIcon>
                      <Checkbox
                        edge="start"
                        checked={selectedEntries.includes(item.id)}
                        onChange={(e) => handleCheckboxChange(e, item.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.title}
                      secondary={
                        <>
                          {`BV: ${item.bvId} - ${new Date(item.createdAt).toLocaleString()}`}
                          <br />
                          {item.tags && item.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" style={{ marginRight: 4 }} />
                          ))}
                        </>
                      }
                    />
                  </ListItemButton>
                  <ListItemSecondaryAction>
                    <IconButton edge="end" aria-label="edit" onClick={() => handleEditEntry(item)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteEntry(item.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              style={{ marginTop: 16, display: 'flex', justifyContent: 'center' }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleBulkDelete} color="secondary" startIcon={<DeleteIcon />}>
              批量删除
            </Button>
            <Button onClick={handleExport} color="primary" startIcon={<ExportIcon />}>
              导出
            </Button>
            <Button onClick={() => setOpenHistory(false)}>关闭</Button>
          </DialogActions>
        </Dialog>
        <Dialog open={Boolean(editingEntry)} onClose={() => setEditingEntry(null)}>
          <DialogTitle>编辑标签</DialogTitle>
          <DialogContent>
            <TextField
              value={editingEntry?.tags?.join(', ') || ''}
              onChange={(e) => setEditingEntry({ 
                ...editingEntry, 
                tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
              })}
              fullWidth
              margin="normal"
              helperText="使用逗号分隔多个标签"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditingEntry(null)}>取消</Button>
            <Button onClick={handleUpdateTags} color="primary">保存</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ThemeProvider>
  );
} // 添加这个结束大括号

export default App;