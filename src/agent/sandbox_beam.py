from beam import Image, endpoint

image = Image().from_dockerfile("./agent/e2b.Dockerfile")

sandbox = Sandbox(image=image, cpu=2.0, memory="16Gi", keep_warm_seconds=-1)

process = sb.process.exec(f'''echo 
                          
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService


class GTTSExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com"))  # USE GTTS

        circle = Circle(radius=1, color=BLUE)

        with self.voiceover(text="This is a circle.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        self.wait(1)


                          > script.py''')


response = sb.process.exec('manim --media_dir /home/user/bucket/media -ql /home/user/sample_scene.py --disable_caching')
print(response.result)