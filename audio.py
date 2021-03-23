from pydub import AudioSegment
import soundfile as sf
import pyrubberband
import tempfile
import time
import os
import numpy as np

#Utility functions
def mp3_to_wav(mp3_file_path, output_path, force=True, sample_rate=192000):
    if not os.path.exists(output_path) or force:
        try:
            sound = AudioSegment.from_file(mp3_file_path, format='mp3')
            sound.set_frame_rate(sample_rate)
            sound.export(output_path, format="wav", bitrate="192k")
        except Exception as e:
            print(e)
    else:
        print("Using cached " + output_path)


def wav_to_mp3(wav_file_path, output_path, force=True, sample_rate=192000):
    if not os.path.exists(output_path) or force:
        try:
            sound = AudioSegment.from_file(wav_file_path, format='wav')
            sound.set_frame_rate(sample_rate)
            sound.export(output_path, format="mp3", bitrate="192k")
        except Exception as e:
            print(e)
    else:
        print("Using cached " + output_path)


class outputAudio():
    def __init__(self, ownership_file, original_file, combined_path, pitch_shift=50, higher_sample_rate=192000):
        self.higher_sample_rate = higher_sample_rate
        self.ownership_file = ownership_file
        self.ownership_AudioSegment = AudioSegment.from_file(ownership_file, format='wav')
        self.original_sample_rate = self.ownership_AudioSegment.frame_rate
        self.ownership_AudioSegment.set_frame_rate(higher_sample_rate)
        self.original_file = original_file
        self.original_AudioSegment = AudioSegment.from_file(original_file, format='mp3')
        self.original_AudioSegment.set_frame_rate(higher_sample_rate)
        self.combined_path = combined_path
        self.pitch_shift = pitch_shift
        print("Combining files....")
        # self.combine_files()
        # self.convert_from_human_inaudible()



    def verify_ownership(self, ownership_file):
        #TODO
        pass


    def convert_from_human_inaudible(self):
        #TODO Find out where degredation in negative shift is coming from -> alternativly could apply fade to require lesser pitch shift
        #TODO Find out a way to do this without access to the original audio file
        '''
        Want to either be able to sample above a certain frequency or otherwise get the difference between the two files
        Otherwise we can overlay the inverse of the original
        '''
        start_time = 0
        duration = self.ownership_AudioSegment.duration_seconds
        semitones = -self.pitch_shift

        sound1 = AudioSegment.from_file(self.combined_path, start_second=start_time, duration=duration, format="wav")
        sound1.set_frame_rate(self.higher_sample_rate)
        original_sound = AudioSegment.from_file(self.original_file, start_second=start_time, duration=duration, format="wav")
        original_sound.set_frame_rate(self.higher_sample_rate)
        sound2 = original_sound.invert_phase() #This should cancel out the original audio in our clip

        combined = sound1.overlay(sound2) #This should be just our pitch shifted ownership audio
        combined.set_frame_rate(self.higher_sample_rate)
        wav_data = np.array(combined.get_array_of_samples())

        try:
            audible_ownership = pyrubberband.pitch_shift(wav_data, self.higher_sample_rate, semitones) #This should reverse the original pitch shift
            temp2 = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(temp2.name, audible_ownership, self.higher_sample_rate)
            wav_to_mp3(temp2.name, './recovered_ownership.mp3', force=True) #Converted to mp3 for convenience
            temp2.close()
        except Exception as e:
            print(e)


    def convert_to_human_inaudible(self, output_path):
        #TODO figure out exact semitones to inaudible
        #TODO figure out how to speed this up (chunk processing)
        seg = self.ownership_AudioSegment
        seg.set_frame_rate(self.higher_sample_rate)
        wav_data = np.array(seg.get_array_of_samples())
        semitones = self.pitch_shift

        try:
            inaudible_samples = pyrubberband.pitch_shift(wav_data, self.higher_sample_rate, semitones)
            sf.write(output_path, inaudible_samples, self.original_sample_rate)
        except Exception as e:
            print(e)


    def combine_files(self):
        print("original duration:")
        print(self.original_AudioSegment.duration_seconds)
        print("ownership duration:") #Inaudible duration should be the same as ownership
        print(self.ownership_AudioSegment.duration_seconds)

        temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False) #Not sure if the suffix is necessary here
        self.convert_to_human_inaudible(temp.name)
        inaudible_data = AudioSegment.from_file(temp.name, format='wav')
        inaudible_data.set_frame_rate(self.higher_sample_rate)
        print("inaudible ownership duration")
        print(inaudible_data.duration_seconds)
        temp.close()

        combined_data = self.original_AudioSegment.overlay(inaudible_data)
        combined_data.set_frame_rate(self.higher_sample_rate)

        try:
            combined_data.export(self.combined_path, format="wav", bitrate="192k")
        except Exception as e:
            print(e)


    def pitch_shift_test(self):
        '''
        Function for testing the audio degredation created by the pitch shifting
        This is now ahead of the other stuff

        TODO figure out why the duration is exploding -> bytes are being increased when we filter
        '''
        print("In test")
        print("Ownership Duration")
        #print(self.ownership_AudioSegment.duration_seconds)

        channles = self.ownership_AudioSegment.channels
        sample_width = self.ownership_AudioSegment.sample_width
        semitones = 5 #Semitones(200) + minHuman speech(100) = inaudible Audio

        #Set high and low bounds on original Ownership Audio
        seg = self.ownership_AudioSegment
        seg.set_frame_rate(self.original_sample_rate)
        cleaned_ownership_sound = seg.low_pass_filter(200) #Filter out noise above this
        cleaned_ownership_sound2 = cleaned_ownership_sound.high_pass_filter(50) #And below this (human speech is typically 100-150Hz)
        cleaned_ownership_sound2.set_frame_rate(self.original_sample_rate)
        cleaned_ownership_sound2.export("./pst_original.mp3", format="mp3") #This is just so we can see it
        ownership_wav_data = np.array(cleaned_ownership_sound2.get_array_of_samples())

        #Pitch shift ownership audio to inaudible
        inaudible_samples = pyrubberband.pitch_shift(ownership_wav_data, self.original_sample_rate, semitones)

        # Pitch shift back down to audible and clean again
        audible_samples = pyrubberband.pitch_shift(inaudible_samples, self.original_sample_rate, -semitones)

        print(audible_samples.shape)
        print("checking eq")
        print(np.allclose(audible_samples, ownership_wav_data)) #samples are way off, why
        mse = (np.square(audible_samples - ownership_wav_data)).mean(axis=0)
        print(mse) #Huge MSE off of a pitch shift of just 5

        sf.write('./pst_temp.wav', audible_samples, self.original_sample_rate)
        sound = AudioSegment.from_file('./pst_temp.wav', format="wav", sample_width=sample_width, frame_rate=self.original_sample_rate, channels=channles)
        other_samples = np.array(sound.get_array_of_samples())
        print(other_samples.shape)
        print("Transformed duration: ")
        print(sound.duration_seconds)
        cleaned_sound = sound.low_pass_filter(300)
        cleaned_sound2 = cleaned_sound.high_pass_filter(2)
        cleaned_sound2.set_frame_rate(self.original_sample_rate)
        cleaned_sound2 = cleaned_sound2+10
        print("Cleaned Transformed Duration")
        print(cleaned_sound2.duration_seconds)
        cleaned_sound2.export('./pst_transformed.mp3', format="mp3")


if __name__ == "__main__":
    start = time.time()
    mp3_name = "stuck_in_the_mud"
    mp3_file_path = './stuck_in_the_mud.mp3'
    wav_file_path = './stuck_in_the_mud.wav'
    mp3_ownership_file_path = './ownership_audio.mp3'
    wav_ownership_file_path = './ownership_audio.wav'
    mp3_to_wav(mp3_file_path, wav_file_path)
    mp3_to_wav(mp3_ownership_file_path, wav_ownership_file_path)
    combined_path = './interleaved.wav'
    out = outputAudio(wav_ownership_file_path, wav_file_path, combined_path)
    out.pitch_shift_test()
    # final_mp3 = './interleaved.mp3'
    # wav_to_mp3(combined_path, final_mp3, force=True)
    end = time.time()
    print("Ran in " + str(end-start) + " seconds")