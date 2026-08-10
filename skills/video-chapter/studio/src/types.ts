export type Chapter = {
  id: string;
  start: number;
  end: number;
  title: string;
  summary: string;
};

export type ChapterStyle = {
  position: 'top' | 'bottom';
  marginX: number;
  marginBottom: number;
  barHeight: number;
  gap: number;
  labelGap: number;
  fontFamily: string;
  fontFile: string | null;
  fontSize: number;
  textColor: string;
  activeColor: string;
  inactiveColor: string;
  panelColor: string;
  cornerRadius: number;
  showTitle: boolean;
  showIndex: boolean;
};

export type ChapterProject = {
  schemaVersion: '1.0';
  name: string;
  video: {
    src: string;
    duration: number;
    width: number;
    height: number;
    fps: number;
  };
  chapters: Chapter[];
  style: ChapterStyle;
  export: {
    codec: 'h264';
    crf: number;
    preset: string;
    alphaCodec: 'prores_4444';
  };
};

