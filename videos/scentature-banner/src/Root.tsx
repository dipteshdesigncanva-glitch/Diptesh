import { Composition, Folder } from "remotion";
import { Flash } from "./elements/Flash";
import { Particles } from "./elements/Particles";
import { ScentatureBanner } from "./ScentatureBanner";
import { IntroScene } from "./scenes/IntroScene";
import { OutroScene } from "./scenes/OutroScene";
import { ProductScene } from "./scenes/ProductScene";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ScentatureBanner"
        component={ScentatureBanner}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
      <Folder name="Scenes">
        <Composition
          id="IntroScene"
          component={IntroScene}
          durationInFrames={60}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            tagline: "THE SIGNATURE COLLECTION",
            style: { backgroundColor: "#050505" },
          }}
        />
        <Composition
          id="ProductScene"
          component={ProductScene}
          durationInFrames={75}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            plate: "plates/bad-girl.jpg",
            line1: "BAD",
            line2: "GIRL",
            tagline: "BOLD · WARM · UNFORGETTABLE",
            accent: "#E08A3C",
            index: 1,
            total: 4,
            cta: "SHOP NOW",
            style: { backgroundColor: "#000" },
          }}
        />
        <Composition
          id="OutroScene"
          component={OutroScene}
          durationInFrames={90}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            cta: "SHOP THE COLLECTION",
            style: { backgroundColor: "#050505" },
          }}
        />
      </Folder>
      <Folder name="Elements">
        <Composition
          id="Particles"
          component={Particles}
          durationInFrames={90}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ color: "#F3D9A4", count: 40, seed: "preview" }}
        />
        <Composition
          id="Flash"
          component={Flash}
          durationInFrames={12}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ color: "#FF2E7E" }}
        />
      </Folder>
    </>
  );
};
