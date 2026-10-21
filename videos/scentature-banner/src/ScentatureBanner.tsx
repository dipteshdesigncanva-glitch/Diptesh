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
          line1="Bad"
          line2="Girl"
          shape="drop"
          base="#120A06"
          price="₹549"
          tagline="Bold, warm & unforgettable."
          accent="#E07A2E"
          index={1}
          total={4}
          cta="SHOP NOW"
        />
        <ProductScene
          name="Floral Kiss"
          from={4.5 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/floral-kiss.png"
          line1="Floral"
          line2="Kiss"
          shape="petal"
          base="#14060C"
          price="₹549"
          tagline="Soft, romantic & in bloom."
          accent="#FF2E7E"
          index={2}
          total={4}
          cta="SHOP NOW"
        />
        <ProductScene
          name="Hawas Classic"
          from={7 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/hawas-classic.png"
          line1="Hawas"
          line2="Classic"
          shape="leaf"
          base="#04110A"
          price="₹549"
          tagline="Fresh, confident & timeless."
          accent="#22C55E"
          index={3}
          total={4}
          cta="SHOP NOW"
        />
        <ProductScene
          name="Hawas Ice"
          from={9.5 * fps}
          durationInFrames={2.5 * fps}
          bottle="bottles/hawas-ice.png"
          line1="Hawas"
          line2="Ice"
          shape="ice"
          base="#050A18"
          price="₹549"
          tagline="Cool, crisp & electric."
          accent="#3B6BFF"
          index={4}
          total={4}
          cta="SHOP NOW"
        />
        <OutroScene
          name="Outro – line-up"
          from={12 * fps}
          durationInFrames={3 * fps}
          headline="Four signature scents, each"
          price="₹549"
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

      <Audio name="Music" src={staticFile("audio/music.wav")} volume={0.75} />

      <Track name="Sound effects">
        <Audio name="Swell" src={staticFile("audio/swell.wav")} volume={0.4} />
        <Audio
          name="Shimmer – logo"
          from={18}
          src={staticFile("audio/shimmer.wav")}
          volume={0.45}
        />
        <Audio
          name="Whoosh – Bad Girl"
          from={2 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.3}
        />
        <Audio
          name="Glass – Bad Girl"
          from={2 * fps + 13}
          src={staticFile("audio/tink.wav")}
          volume={0.4}
        />
        <Audio
          name="Spray – Bad Girl"
          from={2 * fps + 16}
          src={staticFile("audio/spray.wav")}
          volume={0.45}
        />
        <Audio
          name="Whoosh – Floral Kiss"
          from={4.5 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.3}
        />
        <Audio
          name="Glass – Floral Kiss"
          from={4.5 * fps + 13}
          src={staticFile("audio/tink.wav")}
          volume={0.4}
        />
        <Audio
          name="Spray – Floral Kiss"
          from={4.5 * fps + 16}
          src={staticFile("audio/spray.wav")}
          volume={0.45}
        />
        <Audio
          name="Whoosh – Hawas Classic"
          from={7 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.3}
        />
        <Audio
          name="Glass – Hawas Classic"
          from={7 * fps + 13}
          src={staticFile("audio/tink.wav")}
          volume={0.4}
        />
        <Audio
          name="Spray – Hawas Classic"
          from={7 * fps + 16}
          src={staticFile("audio/spray.wav")}
          volume={0.45}
        />
        <Audio
          name="Whoosh – Hawas Ice"
          from={9.5 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.3}
        />
        <Audio
          name="Glass – Hawas Ice"
          from={9.5 * fps + 13}
          src={staticFile("audio/tink.wav")}
          volume={0.4}
        />
        <Audio
          name="Spray – Hawas Ice"
          from={9.5 * fps + 16}
          src={staticFile("audio/spray.wav")}
          volume={0.45}
        />
        <Audio
          name="Whoosh – Outro"
          from={12 * fps - 12}
          src={staticFile("audio/whoosh.wav")}
          volume={0.3}
        />
        <Audio
          name="Glass – line-up 1"
          from={12 * fps + 17}
          src={staticFile("audio/tink.wav")}
          volume={0.25}
        />
        <Audio
          name="Glass – line-up 2"
          from={12 * fps + 21}
          src={staticFile("audio/tink.wav")}
          volume={0.25}
        />
        <Audio
          name="Glass – line-up 3"
          from={12 * fps + 25}
          src={staticFile("audio/tink.wav")}
          volume={0.25}
        />
        <Audio
          name="Glass – line-up 4"
          from={12 * fps + 29}
          src={staticFile("audio/tink.wav")}
          volume={0.25}
        />
        <Audio
          name="Shimmer – Outro"
          from={12 * fps + 34}
          src={staticFile("audio/shimmer.wav")}
          volume={0.4}
        />
      </Track>
    </AbsoluteFill>
  );
};
