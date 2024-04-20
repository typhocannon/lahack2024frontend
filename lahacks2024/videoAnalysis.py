import google.generativeai as genai
import cv2
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# configuring gemini with API key
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

# setting video file_name
video_file_name = "wallet.mp4"

# Create or cleanup existing extracted image frames directory.
FRAME_EXTRACTION_DIRECTORY = "content/frames"
FRAME_PREFIX = "_frame"

def create_frame_output_dir(output_dir):
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  else:
    shutil.rmtree(output_dir)
    os.makedirs(output_dir)

def extract_frame_from_video(video_file_path):
  print(f"Extracting {video_file_path} at 1 frame per second. This might take a bit...")
  create_frame_output_dir(FRAME_EXTRACTION_DIRECTORY)
  vidcap = cv2.VideoCapture(video_file_path)
  fps = vidcap.get(cv2.CAP_PROP_FPS)
  frame_duration = 1 / fps  # Time interval between frames (in seconds)
  output_file_prefix = os.path.basename(video_file_path).replace('.', '_')
  frame_count = 0
  count = 0
  while vidcap.isOpened():
      success, frame = vidcap.read()
      if not success: # End of video
          break
      if int(count / fps) == frame_count: # Extract a frame every second
          min = frame_count // 60
          sec = frame_count % 60
          time_string = f"{min:02d}-{sec:02d}"
          image_name = f"{output_file_prefix}{FRAME_PREFIX}{time_string}.jpg"
          output_filename = FRAME_EXTRACTION_DIRECTORY + "/" + image_name
          
          # print("output filename is: ", output_filename)
          
          cv2.imwrite(output_filename, frame)
          # cv2.imshow("frame", frame)
          # cv2.waitKey(10000000)
          frame_count += 1
      count += 1
  vidcap.release() # Release the capture object\n",
  print(f"Completed video frame extraction!\n\nExtracted: {frame_count} frames")

extract_frame_from_video(video_file_name)

class File:
  def __init__(self, file_path: str, display_name: str = None):
    self.file_path = file_path
    if display_name:
      self.display_name = display_name
    self.timestamp = get_timestamp(file_path)

  def set_file_response(self, response):
    self.response = response

def get_timestamp(filename):
  """Extracts the frame count (as an integer) from a filename with the format
     'output_file_prefix_frame00:00.jpg'.
  """
  parts = filename.split(FRAME_PREFIX)
  if len(parts) != 2:
      return None  # Indicates the filename might be incorrectly formatted
  return parts[1].split('.')[0]

# Process each frame in the output directory
files = os.listdir(FRAME_EXTRACTION_DIRECTORY)
files = sorted(files)
files_to_upload = []
for file in files:
    file_path_directory = FRAME_EXTRACTION_DIRECTORY + "/" + file
    print("File path:", file_path_directory)  # Print the file path
    files_to_upload.append(File(file_path=file_path_directory))

# Upload the files to the API
# Only upload a 10 second slice of files to reduce upload time.
# Change full_video to True to upload the whole video.
full_video = False

uploaded_files = []
print(f'Uploading {len(files_to_upload) if full_video else 3} files. This might take a bit...')

if len(files_to_upload) == 0:
  print("no files to upload")
else:
  print("there are files to upload")

for file in files_to_upload:
  print(f'Uploading: {file.file_path}...')
  response = genai.upload_file(path=file.file_path)
  file.set_file_response(response)
  uploaded_files.append(file)

print(f"Completed file uploads!\n\nUploaded: {len(uploaded_files)} files")

# List files uploaded in the API
for n, f in zip(range(len(uploaded_files)), genai.list_files()):
  print(f.uri)

# Create the prompt.
prompt = "For each frame, return a json format of {timestamp: <given_timestamp>, action: <vibrate, hot, cold, none>, body_part: {chest, left_hand, right_hand, none}}, only if there is a valid action. You can tell that there is a valid action if the main character on the screen gets hit, experiences a hot or cold experience, and tell us which part of the body that they experienced that sensation (chest, left hand or right hand)" 

# Set the model to Gemini 1.5 Pro.
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

# Make GenerateContent request with the structure described above.
def make_request(prompt, files):
  request = [prompt]
  for file in files:
    request.append(file.timestamp)
    request.append(file.response)
  return request

# Make the LLM request.
request = make_request(prompt, uploaded_files)
response = model.generate_content(request,
                                  request_options={"timeout": 600})
print(response.text)
