import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ChangeEvent,
  type PointerEvent,
} from 'react';
import {ChapterOverlay} from './ChapterOverlay';
import {defaultProject} from './defaultProject';
import {formatClock, parseClock} from './time';
import type {ChapterProject, ChapterStyle} from './types';

type IconName =
  | 'add'
  | 'download'
  | 'folder'
  | 'movie'
  | 'pause'
  | 'play'
  | 'spark'
  | 'trash';

function Icon({name}: {name: IconName}) {
  const paths: Record<IconName, React.ReactNode> = {
    add: <path d="M12 5v14M5 12h14" />,
    download: <path d="M12 3v12m0 0 5-5m-5 5-5-5M5 21h14" />,
    folder: <path d="M3 7.5h7l2-2h9v14H3z" />,
    movie: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m10 9 5 3-5 3z" />
      </>
    ),
    pause: (
      <>
        <path d="M9 5v14" />
        <path d="M15 5v14" />
      </>
    ),
    play: <path d="m8 5 11 7-11 7z" />,
    spark: <path d="m12 3 1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6zM19 17l.7 2.3L22 20l-2.3.7L19 23l-.7-2.3L16 20l2.3-.7z" />,
    trash: <path d="M5 7h14M9 7V4h6v3m-8 0 1 14h8l1-14M10 11v6m4-6v6" />,
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

const cloneProject = (project: ChapterProject): ChapterProject =>
  structuredClone(project);

const activeChapterIndex = (project: ChapterProject, currentTime: number) => {
  const index = project.chapters.findIndex(
    (chapter) => currentTime >= chapter.start && currentTime < chapter.end,
  );
  return index < 0 ? project.chapters.length - 1 : index;
};

const isChapterProject = (value: unknown): value is ChapterProject => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<ChapterProject>;
  return (
    candidate.schemaVersion === '1.0' &&
    typeof candidate.name === 'string' &&
    Array.isArray(candidate.chapters) &&
    candidate.chapters.length > 0 &&
    Boolean(candidate.video) &&
    Boolean(candidate.style)
  );
};

export default function App() {
  const [project, setProject] = useState<ChapterProject>(() =>
    cloneProject(defaultProject),
  );
  const [currentTime, setCurrentTime] = useState(0);
  const [videoUrl, setVideoUrl] = useState('');
  const [videoName, setVideoName] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [notice, setNotice] = useState('示例项目已加载');
  const videoRef = useRef<HTMLVideoElement>(null);
  const projectInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  const duration = project.video.duration;
  const activeIndex = Math.max(0, activeChapterIndex(project, currentTime));
  const activeChapter = project.chapters[activeIndex];

  useEffect(() => {
    const timer = window.setTimeout(() => setNotice(''), 3200);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(
    () => () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    },
    [videoUrl],
  );

  const totalLabel = useMemo(
    () => formatClock(project.video.duration, true, project.video.fps),
    [project.video.duration, project.video.fps],
  );

  const updateStyle = (patch: Partial<ChapterStyle>) => {
    setProject((previous) => ({
      ...previous,
      style: {...previous.style, ...patch},
    }));
  };

  const updateChapter = (
    index: number,
    patch: Partial<ChapterProject['chapters'][number]>,
  ) => {
    setProject((previous) => {
      const chapters = previous.chapters.map((chapter, chapterIndex) =>
        chapterIndex === index ? {...chapter, ...patch} : chapter,
      );
      return {...previous, chapters};
    });
  };

  const setBoundary = (index: number, requested: number) => {
    if (index <= 0 || index >= project.chapters.length) return;
    setProject((previous) => {
      const chapters = previous.chapters.map((chapter) => ({...chapter}));
      const minimum = chapters[index - 1].start + 0.5;
      const maximum = chapters[index].end - 0.5;
      const next = Math.min(maximum, Math.max(minimum, requested));
      chapters[index - 1].end = next;
      chapters[index].start = next;
      return {...previous, chapters};
    });
  };

  const handleBoundaryPointer = (
    event: PointerEvent<HTMLButtonElement>,
    index: number,
  ) => {
    if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
    const track = event.currentTarget.parentElement;
    if (!track) return;
    const bounds = track.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width));
    setBoundary(index, ratio * duration);
  };

  const seek = (time: number) => {
    const next = Math.min(duration, Math.max(0, time));
    setCurrentTime(next);
    if (videoRef.current) videoRef.current.currentTime = next;
  };

  const togglePlayback = async () => {
    const video = videoRef.current;
    if (!video) {
      setNotice('先选择本地视频，再开始播放');
      return;
    }
    if (video.paused) {
      await video.play();
    } else {
      video.pause();
    }
  };

  const importProject = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const parsed: unknown = JSON.parse(await file.text());
      if (!isChapterProject(parsed)) throw new Error('项目结构不完整');
      setProject(parsed);
      setCurrentTime(0);
      setNotice(`已加载 ${file.name}`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '项目读取失败');
    } finally {
      event.target.value = '';
    }
  };

  const selectVideo = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideoUrl(URL.createObjectURL(file));
    setVideoName(file.name);
    setNotice(`已选择 ${file.name}`);
    event.target.value = '';
  };

  const syncVideoMetadata = () => {
    const video = videoRef.current;
    if (!video || !Number.isFinite(video.duration) || video.duration <= 0) return;
    setProject((previous) => {
      const ratio = video.duration / previous.video.duration;
      const chapters = previous.chapters.map((chapter, index) => ({
        ...chapter,
        start: index === 0 ? 0 : chapter.start * ratio,
        end:
          index === previous.chapters.length - 1
            ? video.duration
            : chapter.end * ratio,
      }));
      return {
        ...previous,
        video: {
          ...previous.video,
          src: videoName,
          duration: video.duration,
          width: video.videoWidth,
          height: video.videoHeight,
        },
        chapters,
      };
    });
    setCurrentTime(0);
  };

  const exportProject = () => {
    const payload = JSON.stringify(project, null, 2);
    const blob = new Blob([`${payload}\n`], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'chapter-project.json';
    anchor.click();
    URL.revokeObjectURL(url);
    setNotice('chapter-project.json 已导出');
  };

  const copyRenderCommand = async () => {
    const command =
      'python3 scripts/render_chapter_bar.py burn --project "chapter-project.json" --output "video-with-chapters.mp4"';
    await navigator.clipboard.writeText(command);
    setNotice('烧录命令已复制');
  };

  const addChapter = () => {
    if (project.chapters.length >= 8) {
      setNotice('一个章节条最多保留 8 段');
      return;
    }
    setProject((previous) => {
      const chapters = previous.chapters.map((chapter) => ({...chapter}));
      const index = Math.max(0, activeChapterIndex(previous, currentTime));
      const chapter = chapters[index];
      const preferred =
        currentTime > chapter.start + 1 && currentTime < chapter.end - 1
          ? currentTime
          : (chapter.start + chapter.end) / 2;
      const oldEnd = chapter.end;
      chapter.end = preferred;
      chapters.splice(index + 1, 0, {
        id: `chapter-${Date.now()}`,
        start: preferred,
        end: oldEnd,
        title: '新章节',
        summary: '',
      });
      return {...previous, chapters};
    });
    setNotice('已在播放头位置拆分章节');
  };

  const deleteChapter = (index: number) => {
    if (project.chapters.length === 1) {
      setNotice('至少保留一个章节');
      return;
    }
    setProject((previous) => {
      const chapters = previous.chapters.map((chapter) => ({...chapter}));
      const removed = chapters[index];
      chapters.splice(index, 1);
      if (index === 0) {
        chapters[0].start = 0;
      } else {
        chapters[index - 1].end = removed.end;
      }
      return {...previous, chapters};
    });
    setNotice('章节已合并到相邻段落');
  };

  const setColor = (
    key: 'activeColor' | 'inactiveColor' | 'panelColor' | 'textColor',
    value: string,
  ) => {
    const current = project.style[key];
    const alpha = current.length === 9 ? current.slice(7) : '';
    updateStyle({[key]: `${value}${alpha}`} as Partial<ChapterStyle>);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <img src="/lov-video-chapter.svg" alt="" />
          <div>
            <strong>Video Chapter</strong>
            <span>STUDIO / 0.2</span>
          </div>
        </div>

        <label className="project-name">
          <span>项目</span>
          <input
            value={project.name}
            onChange={(event) =>
              setProject((previous) => ({...previous, name: event.target.value}))
            }
          />
        </label>

        <div className="top-actions">
          <input
            ref={projectInputRef}
            className="visually-hidden"
            type="file"
            accept="application/json,.json"
            onChange={importProject}
          />
          <input
            ref={videoInputRef}
            className="visually-hidden"
            type="file"
            accept="video/*"
            onChange={selectVideo}
          />
          <button className="button button--quiet" onClick={() => projectInputRef.current?.click()}>
            <Icon name="folder" />
            加载项目
          </button>
          <button className="button button--quiet" onClick={copyRenderCommand}>
            <Icon name="spark" />
            复制烧录命令
          </button>
          <button className="button button--primary" onClick={exportProject}>
            <Icon name="download" />
            导出项目
          </button>
        </div>
      </header>

      <main className="workspace">
        <aside className="chapter-panel panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">内容结构</span>
              <h1>章节</h1>
            </div>
            <button className="icon-button" onClick={addChapter} aria-label="新增章节">
              <Icon name="add" />
            </button>
          </div>
          <p className="panel-hint">拖动下方接缝或修改时间码，切点会自动保持连续。</p>

          <div className="chapter-list">
            {project.chapters.map((chapter, index) => (
              <article
                className={`chapter-card ${index === activeIndex ? 'is-active' : ''}`}
                key={chapter.id}
                onClick={() => seek(chapter.start)}
              >
                <div className="chapter-card-head">
                  <span className="chapter-number">{String(index + 1).padStart(2, '0')}</span>
                  <div className="chapter-times">
                    <input
                      key={`start-${chapter.id}-${chapter.start}`}
                      defaultValue={formatClock(chapter.start)}
                      aria-label={`第 ${index + 1} 章开始时间`}
                      disabled={index === 0}
                      onClick={(event) => event.stopPropagation()}
                      onBlur={(event) => {
                        const parsed = parseClock(event.target.value);
                        if (parsed !== null) setBoundary(index, parsed);
                      }}
                    />
                    <span>→</span>
                    <time>{formatClock(chapter.end)}</time>
                  </div>
                  <button
                    className="delete-button"
                    aria-label={`删除第 ${index + 1} 章`}
                    onClick={(event) => {
                      event.stopPropagation();
                      deleteChapter(index);
                    }}
                  >
                    <Icon name="trash" />
                  </button>
                </div>
                <input
                  className="chapter-title-input"
                  value={chapter.title}
                  aria-label={`第 ${index + 1} 章标题`}
                  onClick={(event) => event.stopPropagation()}
                  onChange={(event) => updateChapter(index, {title: event.target.value})}
                />
                <textarea
                  value={chapter.summary}
                  aria-label={`第 ${index + 1} 章摘要`}
                  placeholder="这一段讲什么？"
                  onClick={(event) => event.stopPropagation()}
                  onChange={(event) => updateChapter(index, {summary: event.target.value})}
                />
              </article>
            ))}
          </div>
        </aside>

        <section className="stage-panel">
          <div className="stage-toolbar">
            <div>
              <span className="status-dot" />
              <span>{videoName || '尚未连接本地视频'}</span>
            </div>
            <div className="stage-meta">
              {project.video.width} × {project.video.height}
              <span />
              {project.video.fps.toFixed(2)} FPS
            </div>
          </div>

          <div
            className="video-stage"
            style={{aspectRatio: `${project.video.width} / ${project.video.height}`}}
          >
            {videoUrl ? (
              <video
                ref={videoRef}
                src={videoUrl}
                onLoadedMetadata={syncVideoMetadata}
                onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
              />
            ) : (
              <div className="empty-stage">
                <div className="empty-stage-mark">
                  <Icon name="movie" />
                </div>
                <strong>把视频接入剪辑台</strong>
                <span>视频留在本机，只用于浏览器预览。</span>
                <button className="button button--stage" onClick={() => videoInputRef.current?.click()}>
                  选择本地视频
                </button>
              </div>
            )}
            <div className="safe-area" />
            <ChapterOverlay project={project} currentTime={currentTime} />
          </div>

          <div className="transport">
            <button className="play-button" onClick={togglePlayback} aria-label={isPlaying ? '暂停' : '播放'}>
              <Icon name={isPlaying ? 'pause' : 'play'} />
            </button>
            <time>{formatClock(currentTime, true, project.video.fps)}</time>
            <input
              className="scrubber"
              type="range"
              min="0"
              max={duration}
              step={1 / project.video.fps}
              value={Math.min(currentTime, duration)}
              onChange={(event) => seek(Number(event.target.value))}
              aria-label="播放位置"
              style={{'--scrub-progress': `${(currentTime / duration) * 100}%`} as React.CSSProperties}
            />
            <time className="duration">{totalLabel}</time>
          </div>

          <div className="timeline-panel">
            <div className="timeline-head">
              <div>
                <span className="eyebrow">CHAPTER SPLICE</span>
                <strong>{activeChapter?.title}</strong>
              </div>
              <span>{project.chapters.length} 段 · 拖动接缝调整</span>
            </div>
            <div className="timeline-track">
              {project.chapters.map((chapter, index) => (
                <button
                  className="timeline-segment"
                  key={chapter.id}
                  style={{
                    width: `${((chapter.end - chapter.start) / duration) * 100}%`,
                    '--segment-progress': `${
                      currentTime <= chapter.start
                        ? 0
                        : currentTime >= chapter.end
                          ? 100
                          : ((currentTime - chapter.start) /
                              (chapter.end - chapter.start)) *
                            100
                    }%`,
                  } as CSSProperties}
                  onClick={() => seek(chapter.start)}
                  title={`${formatClock(chapter.start)} ${chapter.title}`}
                >
                  <span>{String(index + 1).padStart(2, '0')}</span>
                </button>
              ))}
              {project.chapters.slice(1).map((chapter, offset) => (
                <button
                  className="boundary-handle"
                  key={`boundary-${chapter.id}`}
                  style={{left: `${(chapter.start / duration) * 100}%`}}
                  aria-label={`调整第 ${offset + 2} 章开始时间`}
                  onPointerDown={(event) => {
                    event.currentTarget.setPointerCapture(event.pointerId);
                    handleBoundaryPointer(event, offset + 1);
                  }}
                  onPointerMove={(event) => handleBoundaryPointer(event, offset + 1)}
                  onPointerUp={(event) => event.currentTarget.releasePointerCapture(event.pointerId)}
                >
                  <span />
                </button>
              ))}
              <div
                className="timeline-playhead"
                style={{left: `${(currentTime / duration) * 100}%`}}
              >
                <span />
              </div>
            </div>
            <div className="timeline-scale">
              <span>00:00</span>
              <span>{formatClock(duration / 2)}</span>
              <span>{formatClock(duration)}</span>
            </div>
          </div>
        </section>

        <aside className="inspector panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">视觉系统</span>
              <h2>章节条</h2>
            </div>
          </div>

          <section className="control-group">
            <div className="control-label">
              <span>位置</span>
              <small>贴近画面安全区</small>
            </div>
            <div className="segmented-control">
              {(['bottom', 'top'] as const).map((position) => (
                <button
                  className={project.style.position === position ? 'is-selected' : ''}
                  key={position}
                  onClick={() => updateStyle({position})}
                >
                  {position === 'bottom' ? '底部' : '顶部'}
                </button>
              ))}
            </div>
          </section>

          <section className="control-group">
            <div className="control-label">
              <span>色彩</span>
              <small>LovStudio signal</small>
            </div>
            <label className="color-control">
              <span>
                <i style={{background: project.style.activeColor}} />
                已播放
              </span>
              <input
                type="color"
                value={project.style.activeColor.slice(0, 7)}
                onChange={(event) => setColor('activeColor', event.target.value)}
              />
            </label>
            <label className="color-control">
              <span>
                <i style={{background: project.style.inactiveColor}} />
                未播放
              </span>
              <input
                type="color"
                value={project.style.inactiveColor.slice(0, 7)}
                onChange={(event) => setColor('inactiveColor', event.target.value)}
              />
            </label>
            <label className="color-control">
              <span>
                <i style={{background: project.style.panelColor}} />
                标题底板
              </span>
              <input
                type="color"
                value={project.style.panelColor.slice(0, 7)}
                onChange={(event) => setColor('panelColor', event.target.value)}
              />
            </label>
          </section>

          <section className="control-group">
            <div className="control-label">
              <span>几何</span>
              <small>按输出像素计算</small>
            </div>
            {[
              ['barHeight', '条高度', 4, 40],
              ['gap', '段间距', 0, 30],
              ['marginX', '左右边距', 24, 240],
              ['marginBottom', '边缘距离', 20, 200],
              ['fontSize', '标题字号', 18, 72],
            ].map(([key, label, min, max]) => {
              const typedKey = key as keyof ChapterStyle;
              return (
                <label className="range-control" key={key}>
                  <span>
                    {label}
                    <output>{String(project.style[typedKey])}</output>
                  </span>
                  <input
                    type="range"
                    min={Number(min)}
                    max={Number(max)}
                    value={Number(project.style[typedKey])}
                    onChange={(event) =>
                      updateStyle({[typedKey]: Number(event.target.value)} as Partial<ChapterStyle>)
                    }
                  />
                </label>
              );
            })}
          </section>

          <section className="control-group">
            <label className="switch-control">
              <span>
                显示章节标题
                <small>随切点自动切换</small>
              </span>
              <input
                type="checkbox"
                checked={project.style.showTitle}
                onChange={(event) => updateStyle({showTitle: event.target.checked})}
              />
            </label>
            <label className="switch-control">
              <span>
                显示章节编号
                <small>01、02、03…</small>
              </span>
              <input
                type="checkbox"
                checked={project.style.showIndex}
                onChange={(event) => updateStyle({showIndex: event.target.checked})}
              />
            </label>
          </section>

          <div className="render-note">
            <Icon name="spark" />
            <div>
              <strong>预览即规格</strong>
              <span>导出的 JSON 会把当前布局交给 FFmpeg 渲染器。</span>
            </div>
          </div>
        </aside>
      </main>

      {notice ? <div className="toast">{notice}</div> : null}
    </div>
  );
}
