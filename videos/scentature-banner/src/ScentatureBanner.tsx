import { Audio } from "@remotion/media";
import { AbsoluteFill, staticFile, Track, useVideoConfig } from "remotion";
import { PanelWipe } from "./elements/PanelWipe";
import { IntroScene } from "./scenes/IntroScene";
import { OutroScene } from "./scenes/OutroScene";
import { ProductScene } from "./scenes/ProductScene";

// 15 s loop at 30 fps. The music is 120 BPM (a beat every 15 frames) and every
// cut below sits on a beat: 60, 135, 210, 285, 360.
export const ScentatureBanner = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0A" }}>
      <Track name="Scenes">
        <IntroScene
          name="Intro – logo"
          durationInFrames={2 * fps}
          tagline="THE SIGNATURE COLLECTION"
          style={{ backgroundColor: "#0A0A0A" }}
        />
        <ProductScene
          name="Bad Girl"
          from={2 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/bad-girl.png"
          line1="BAD"
          line2="GIRL"
          tagline="Bold, warm & unforgettable."
          accent="#E07A2E"
          index={1}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#170D07" }}
        />
        <ProductScene
          name="Floral Kiss"
          from={4.5 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/floral-kiss.png"
          line1="FLORAL"
          line2="KISS"
          tagline="Soft, romantic & in bloom."
          accent="#FF2E7E"
          index={2}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#16060D" }}
        />
        <ProductScene
          name="Hawas Classic"
          from={7 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/hawas-classic.png"
          line1="HAWAS"
          line2="CLASSIC"
          tagline="Fresh, confident & timeless."
          accent="#22C55E"
          index={3}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#04130A" }}
        />
        <ProductScene
          name="Hawas Ice"
          from={9.5 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/hawas-ice.png"
          line1="HAWAS"
          line2="ICE"
          tagline="Cool, crisp & electric."
          accent="#3B6BFF"
          index={4}
          total={4}
          cta="SHOP NOW"
          style={{ backgroundColor: "#050A1B" }}
        />
        <OutroScene
          name="Outro – line-up"
          from={12 * fps}
          durationInFrames={3 * fps}
          cta="SHOP THE COLLECTION"
          style={{ backgroundColor: "#0A0A0A" }}
        />
      </Track>

      {/* Each wipe covers its cut at its own frame 8 */}
      <Track name="Wipes">
        <PanelWipe
          name="Wipe → Bad Girl"
          from={2 * fps - 8}
          durationInFrames={18}
          first="#ffffff"
          second="#E07A2E"
        />
        <PanelWipe
          name="Wipe → Floral Kiss"
          from={4.5 * fps - 8}
          durationInFrames={18}
          first="#E07A2E"
          second="#FF2E7E"
        />
        <PanelWipe
          name="Wipe → Hawas Classic"
          from={7 * fps - 8}
          durationInFrames={18}
          first="#FF2E7E"
          second="#22C55E"
        />
        <PanelWipe
          name="Wipe → Hawas Ice"
          from={9.5 * fps - 8}
          durationInFrames={18}
          first="#22C55E"
          second="#3B6BFF"
        />
        <PanelWipe
          name="Wipe → Outro"
          from={12 * fps - 8}
          durationInFrames={18}
          first="#3B6BFF"
          second="#ffffff"
        />
      </Track>

      <Audio name="Music" src={staticFile("audio/music.wav")} volume={0.62} />

      <Track name="Sound effects">
        <Audio name="Riser" src={staticFile("audio/riser.wav")} volume={0.45} />
        <Audio
          name="Shimmer – logo"
          from={18}
          src={staticFile("audio/shimmer.wav")}
          volume={0.5}
        />
        <Audio
          name="Whoosh – Bad Girl"
          from={2 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.4}
        />
        <Audio
          name="Impact – Bad Girl"
          from={2 * fps}
          src={staticFile("audio/impact.wav")}
          volume={0.3}
        />
        <Audio
          name="Pop – Bad Girl"
          from={2 * fps + 13}
          src={staticFile("audio/pop.wav")}
          volume={0.35}
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
          name="Pop – Floral Kiss"
          from={4.5 * fps + 13}
          src={staticFile("audio/pop.wav")}
          volume={0.35}
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
          name="Pop – Hawas Classic"
          from={7 * fps + 13}
          src={staticFile("audio/pop.wav")}
          volume={0.35}
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
          name="Pop – Hawas Ice"
          from={9.5 * fps + 13}
          src={staticFile("audio/pop.wav")}
          volume={0.35}
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
          from={12 * fps + 30}
          src={staticFile("audio/shimmer.wav")}
          volume={0.45}
        />
      </Track>
    </AbsoluteFill>
  );
};
