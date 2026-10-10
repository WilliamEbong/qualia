import {Composition} from 'remotion';
import {Explainer, TOTAL_FRAMES} from './Explainer';
import {Tutorial, tutorialMetadata} from './tutorials/Tutorial';
import {tutorials} from './tutorials/list';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Explainer" component={Explainer} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} />
    {tutorials.map((t) => (
      <Composition key={t.id} id={`tutorial-${t.id}`} component={Tutorial} durationInFrames={240} fps={30} width={1920}
        height={1080} defaultProps={{id: t.id, timeline: null}} calculateMetadata={tutorialMetadata} />
    ))}
  </>
);
