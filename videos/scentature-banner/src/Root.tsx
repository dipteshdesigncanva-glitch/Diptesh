import { Composition, Folder } from "remotion";
import { Marquee } from "./elements/Marquee";
import { PanelWipe } from "./elements/PanelWipe";
import { Sparkle } from "./elements/Sparkle";
import { SpinBadge } from "./elements/SpinBadge";
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
            style: { backgroundColor: "#0A0A0A" },
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
            bottle: "bottles/bad-girl.png",
            line1: "Bad",
            line2: "Girl",
            shape: "drop",
            base: "#120A06",
            price: "₹299",
            tagline: "Bold, warm & unforgettable.",
            accent: "#E07A2E",
            index: 1,
            total: 4,
            cta: "SHOP NOW",
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
            headline: "Four signature scents, each",
            price: "₹299",
            cta: "SHOP THE COLLECTION",
            style: { backgroundColor: "#0A0A0A" },
          }}
        />
      </Folder>
      <Folder name="Elements">
        <Composition
          id="Marquee"
          component={Marquee}
          durationInFrames={90}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            text: "SCENTATURE — ",
            fontFamily: "Playfair Display",
            fontSize: 250,
            color: "#ffffff",
            outline: true,
            speed: 9,
            style: { top: 400 },
          }}
        />
        <Composition
          id="SpinBadge"
          component={SpinBadge}
          durationInFrames={90}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            text: "EAU DE PARFUM • 50 ML • SCENTATURE • ",
            size: 300,
            color: "#111111",
            fill: "#ffffff",
            delay: 0,
            style: { left: 810, top: 390 },
          }}
        />
        <Composition
          id="Sparkle"
          component={Sparkle}
          durationInFrames={60}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            size: 200,
            color: "#ffffff",
            delay: 0,
            style: { left: 860, top: 440 },
          }}
        />
        <Composition
          id="PanelWipe"
          component={PanelWipe}
          durationInFrames={18}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ first: "#ffffff", second: "#FF2E7E" }}
        />
      </Folder>
    </>
  );
};
