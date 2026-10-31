import { existsSync, readdirSync, readFileSync } from "fs";
import { join, basename, extname } from "path";
import PptxGenJS from "pptxgenjs";

interface SlideInfo {
  filename: string;
  path: string;
  index: number;
  promptPath?: string;
  isSpeakerNotes?: boolean;
}

function parseArgs(): { dir: string; output?: string } {
  const args = process.argv.slice(2);
  let dir = "";
  let output: string | undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--output" || args[i] === "-o") {
      output = args[++i];
    } else if (!args[i].startsWith("-")) {
      dir = args[i];
    }
  }

  if (!dir) {
    console.error("Usage: bun merge-to-pptx.ts <slide-deck-dir> [--output filename.pptx]");
    process.exit(1);
  }

  return { dir, output };
}

function findSlideImages(dir: string): SlideInfo[] {
  if (!existsSync(dir)) {
    console.error(`Directory not found: ${dir}`);
    process.exit(1);
  }

  const files = readdirSync(dir);
  const slidePattern = /^(\d+)-slide-.*\.(png|jpg|jpeg)$/i;
  const notesDir = join(dir, "notes");
  const promptsDir = join(dir, "prompts");

  const slides: SlideInfo[] = files
    .filter((f) => slidePattern.test(f))
    .map((f) => {
      const match = f.match(slidePattern);
      const baseName = f.replace(/\.(png|jpg|jpeg)$/i, "");
      const speakerNotes = join(notesDir, `${baseName}.md`);
      const prompt = join(promptsDir, `${baseName}.md`);
      const notesPath = existsSync(speakerNotes)
        ? speakerNotes
        : existsSync(prompt)
          ? prompt
          : undefined;

      return {
        filename: f,
        path: join(dir, f),
        index: parseInt(match![1], 10),
        promptPath: notesPath,
        isSpeakerNotes: notesPath === speakerNotes,
      };
    })
    .sort((a, b) => a.index - b.index);

  if (slides.length === 0) {
    console.error(`No slide images found in: ${dir}`);
    console.error("Expected format: 01-slide-*.png, 02-slide-*.png, etc.");
    process.exit(1);
  }

  return slides;
}

function findBasePrompt(): string | undefined {
  const scriptDir = import.meta.dir;
  const basePromptPath = join(scriptDir, "..", "references", "base-prompt.md");
  if (existsSync(basePromptPath)) {
    return readFileSync(basePromptPath, "utf-8");
  }
  return undefined;
}

async function createPptx(slides: SlideInfo[], outputPath: string) {
  const pptx = new PptxGenJS();

  pptx.layout = "LAYOUT_16x9";
  pptx.author = "lov-any2deck";
  pptx.subject = "Generated Slide Deck";

  const basePrompt = findBasePrompt();
  let notesCount = 0;

  for (const slide of slides) {
    const s = pptx.addSlide();
    const imageData = readFileSync(slide.path);
    const base64 = imageData.toString("base64");
    const ext = extname(slide.filename).toLowerCase().replace(".", "");
    const mimeType = ext === "png" ? "image/png" : "image/jpeg";

    s.addImage({
      data: `data:${mimeType};base64,${base64}`,
      x: 0,
      y: 0,
      w: "100%",
      h: "100%",
      sizing: { type: "cover", w: "100%", h: "100%" },
    });

    if (slide.promptPath) {
      const content = readFileSync(slide.promptPath, "utf-8");
      // notes/ holds speaker notes meant for the presenter; prompts/ is only a fallback,
      // and there the image-generation base prompt is useful context.
      s.addNotes(
        slide.isSpeakerNotes || !basePrompt ? content : `${basePrompt}\n\n---\n\n${content}`,
      );
      notesCount++;
    }

    const label = slide.isSpeakerNotes ? " (speaker notes)" : slide.promptPath ? " (prompt as notes)" : "";
    console.log(`Added: ${slide.filename}${label}`);
  }

  await pptx.writeFile({ fileName: outputPath });
  console.log(`\nCreated: ${outputPath}`);
  console.log(`Total slides: ${slides.length}`);
  if (notesCount > 0) {
    console.log(`Slides with notes: ${notesCount}`);
  }
}

async function main() {
  const { dir, output } = parseArgs();
  const slides = findSlideImages(dir);

  const dirName = basename(dir) === "slide-deck" ? basename(join(dir, "..")) : basename(dir);
  const outputPath = output || join(dir, `${dirName}.pptx`);

  console.log(`Found ${slides.length} slides in: ${dir}\n`);

  await createPptx(slides, outputPath);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
