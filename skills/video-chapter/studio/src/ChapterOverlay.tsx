import type {CSSProperties} from 'react';
import type {ChapterProject} from './types';

type ChapterOverlayProps = {
  project: ChapterProject;
  currentTime: number;
};

const activeIndexAt = (project: ChapterProject, currentTime: number) => {
  const index = project.chapters.findIndex(
    (chapter) => currentTime >= chapter.start && currentTime < chapter.end,
  );
  return index === -1 ? Math.max(0, project.chapters.length - 1) : index;
};

export function ChapterOverlay({project, currentTime}: ChapterOverlayProps) {
  const {video, style, chapters} = project;
  const activeIndex = activeIndexAt(project, currentTime);
  const activeChapter = chapters[activeIndex];
  const marginX = `${(style.marginX / video.width) * 100}%`;
  const edge = `${(style.marginBottom / video.height) * 100}%`;
  const barHeight = `${Math.max(0.25, (style.barHeight / video.height) * 100)}%`;
  const titleOffset =
    ((style.marginBottom + style.barHeight + style.labelGap) / video.height) * 100;
  const overlayStyle = {
    '--chapter-font': style.fontFamily,
    '--chapter-font-size': `${(style.fontSize / video.width) * 100}cqw`,
  } as CSSProperties;

  return (
    <div className="chapter-overlay" style={overlayStyle} aria-hidden="true">
      {style.showTitle && activeChapter ? (
        <div
          className={`chapter-title-plate chapter-title-plate--${style.position}`}
          style={{
            left: marginX,
            [style.position]: `${titleOffset}%`,
            color: style.textColor,
            background: style.panelColor,
            borderRadius: `${style.cornerRadius / video.width * 100}cqw`,
          }}
        >
          {style.showIndex ? (
            <span className="chapter-title-index">
              {String(activeIndex + 1).padStart(2, '0')}
            </span>
          ) : null}
          <span>{activeChapter.title}</span>
        </div>
      ) : null}

      <div
        className="chapter-bar"
        style={{
          left: marginX,
          right: marginX,
          [style.position]: edge,
          height: barHeight,
          gap: `${(style.gap / video.width) * 100}%`,
        }}
      >
        {chapters.map((chapter) => {
          const progress =
            currentTime <= chapter.start
              ? 0
              : currentTime >= chapter.end
                ? 1
                : (currentTime - chapter.start) / (chapter.end - chapter.start);
          return (
            <span
              className="chapter-bar-segment"
              key={chapter.id}
              style={{
                flexGrow: chapter.end - chapter.start,
                background: style.inactiveColor,
                borderRadius: `${style.cornerRadius / video.width * 100}cqw`,
              }}
            >
              <span
                className="chapter-bar-progress"
                style={{
                  width: `${progress * 100}%`,
                  background: style.activeColor,
                }}
              />
            </span>
          );
        })}
      </div>
    </div>
  );
}

