import { Audio } from "@remotion/media";
import { AbsoluteFill, staticFile, Track, useVideoConfig } from "remotion";
import { Flash } from "./elements/Flash";
import { IntroScene } from "./scenes/IntroScene";
import { OutroScene } from "./scenes/OutroScene";
import { ProductScene } from "./scenes/ProductScene";

// 15 s loop at 30 fps. The music is 120 BPM (a beat every 15 frames) and every
// cut below sits on a beat: 60, 135, 210, 285, 360.
export const ScentatureBanner = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Track name="Scenes">
        <IntroScene
          name="Intro – logo"
          durationInFrames={2 * fps}
          tagline="THE SIGNATURE COLLECTION"
          style={{ backgroundColor: "#050505" }}
        />
        <ProductScene
          name="Bad Girl"
          from={2 * fps}
          durationInFrames={2.5 * fps}
          plate="plates/bad-girl.jpg"
          line1="BAD"
          line2="GIRL"
          tagline="BOLD · WARM · UNFORGETTABLE"
          accent="#E08A3C"
          index={1}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#000" }}
        />
        <ProductScene
          name="Floral Kiss"
          from={4.5 * fps}
          durationInFrames={2.5 * fps}
          plate="plates/floral-kiss.jpg"
          line1="FLORAL"
          line2="KISS"
          tagline="SOFT · ROMANTIC · IN BLOOM"
          accent="#FF2E7E"
          index={2}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#000" }}
        />
        <ProductScene
          name="Hawas Classic"
          from={7 * fps}
          durationInFrames={2.5 * fps}
          plate="plates/hawas-classic.jpg"
          line1="HAWAS"
          line2="CLASSIC"
          tagline="FRESH · CONFIDENT · TIMELESS"
          accent="#2BD960"
          index={3}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#000" }}
        />
        <ProductScene
          name="Hawas Ice"
          from={9.5 * fps}
          durationInFrames={2.5 * fps}
          plate="plates/hawas-ice.jpg"
          line1="HAWAS"
          line2="ICE"
          tagline="COOL · CRISP · ELECTRIC"
          accent="#4D7CFF"
          index={4}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#000" }}
        />
        <OutroScene
          name="Outro – line-up"
          from={12 * fps}
          durationInFrames={3 * fps}
          cta="SHOP THE COLLECTION"
          style={{ backgroundColor: "#050505" }}
        />
      </Track>

      <Track name="Cut flashes">
        <Flash
          name="Flash → Bad Girl"
          from={2 * fps - 2}
          durationInFrames={12}
          color="#E08A3C"
        />
        <Flash
          name="Flash → Floral Kiss"
          from={4.5 * fps - 2}
          durationInFrames={12}
          color="#FF2E7E"
        />
        <Flash
          name="Flash → Hawas Classic"
          from={7 * fps - 2}
          durationInFrames={12}
          color="#2BD960"
        />
        <Flash
          name="Flash → Hawas Ice"
          from={9.5 * fps - 2}
          durationInFrames={12}
          color="#4D7CFF"
        />
        <Flash
          name="Flash → Outro"
          from={12 * fps - 2}
          durationInFrames={12}
          color="#F3D9A4"
        />
      </Track>

      <Audio name="Music" src={staticFile("audio/music.wav")} volume={0.62} />

      <Track name="Sound effects">
        <Audio name="Riser" src={staticFile("audio/riser.wav")} volume={0.45} />
        <Audio
          name="Shimmer – logo"
          from={8}
          src={staticFile("audio/shimmer.wav")}
          volume={0.5}
        />
        <Audio
          name="Impact – Bad Girl"
          from={2 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Whoosh – Floral Kiss"
          from={4.5 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.4}
        />
        <Audio
          name="Impact – Floral Kiss"
          from={4.5 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Whoosh – Hawas Classic"
          from={7 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.4}
        />
        <Audio
          name="Impact – Hawas Classic"
          from={7 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Whoosh – Hawas Ice"
          from={9.5 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.4}
        />
        <Audio
          name="Impact – Hawas Ice"
          from={9.5 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Whoosh – Outro"
          from={12 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.4}
        />
        <Audio
          name="Impact – Outro"
          from={12 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Shimmer – Outro"
          from={12 * fps + 36}
          src={staticFile("audio/shimmer.wav")}
          volume={0.45}
        />
      </Track>
    </AbsoluteFill>
  );
};
