import google.generativeai as genai
import cv2
import os
import shutil
from dotenv import load_dotenv
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

load_dotenv()

# configuring gemini with API key
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

clients = {}
current_client_id = 0

def get_timestamp(file_name):
  name_split = file_name.split('_')
  if len(name_split) >= 3 and name_split[2].endswith('s.jpg'):
        # Strip the 's.jpg' to isolate the number of seconds
        seconds_part = name_split[2][:-5]
        # turn the seconds into MM:SS
        int_seconds = int(seconds_part)
        minutes = int_seconds // 60
        seconds = int_seconds % 60
        return f"{minutes:02}:{seconds:02}"
  else:
      # If the format does not match, return None
      print(f"Error: The filename '{file_name}' is not in the expected format.")
      return None

# File Class to change images to in order to upload to Gemini
class FileType:
  def __init__(self, file_path: str, display_name: str):
    self.file_path = file_path
    self.display_name = display_name
    self.timestamp = get_timestamp(self.display_name)

  def set_file_response(self, response):
    self.response = response

# Make GenerateContent request with the structure described above.
def make_request(prompt, files):
  request = [prompt]
  for file in files:
    request.append(file.timestamp)
    request.append(file.response)
  return request

# using opencv to get frames
def get_all_frames_in_order(video_file_path, output_dir='output_frames'):
    video_capture = cv2.VideoCapture(video_file_path)
    frames = {}
    prev_time = -1
    os.makedirs(output_dir, exist_ok=True)

    while True:
        grabbed = video_capture.grab()
        if not grabbed:
            break
        current_time = int(video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000)
        if current_time > prev_time:
            ret, frame = video_capture.retrieve()
            if ret:
                frame_filename = f"{output_dir}/frame_at_{current_time}s.jpg"
                cv2.imwrite(frame_filename, frame)
                frames[current_time] = {'frame': frame_filename, 'timestamp': current_time}
            prev_time = current_time

    video_capture.release()
    return frames
  
def getCurrentTime():
  now = datetime.now()
  current_time = now.strftime("%H:%M:%S")
  print("Current Time =", current_time)
  print("\n")
  
def convertToFile(frame_directory):
  files = os.listdir(frame_directory)
  files = sorted(files)
  files_to_upload = []
  for file_name in files:
    file_path = frame_directory + "/" + file_name
    Actual_File = FileType(file_path, file_name)
    files_to_upload.append(Actual_File)
  return files_to_upload

def uploadToGeminiFileAPI(convertedFiles):
  uploadedFiles = []
  for file in convertedFiles:
      # print(f'Uploading: {file.file_path}...')
      response = genai.upload_file(path=file.file_path)
      file.set_file_response(response)
      uploadedFiles.append(file)
    
  return uploadedFiles

@app.get("/")
def checkConnection():
  return {"message" : "World"}

@app.post("/uploadTest")
async def analyzeTest(file: UploadFile = File(...)):
  return {
    "message" : "Recevied the file!",
    "file_name" : file.filename,
    "content_type": file.content_type,
    }

@app.post("/upload")
async def analyzeVideo(file_sent: UploadFile = File(...)): 
  print("connected & starting upload\n")
  # Define a temporary file path
  temp_file_path = f"temp/{file_sent.filename}"
  temp_frame_path = "tempframes/"
  
  # Create the temporary directory if it doesn't exist
  os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
  os.makedirs(os.path.dirname(temp_frame_path), exist_ok=True)
  
  
  # Save the uploaded video file to disk
  with open(temp_file_path, 'wb') as f:
      f.write(await file_sent.read())
  
  print("GETTING FRAMES")
  getCurrentTime()
  
  # Process the video to extract frames
  output_frames_directory = temp_frame_path
  frames = get_all_frames_in_order(temp_file_path, output_dir=output_frames_directory)
  
  print("DONE GETTING FRAMES")
  getCurrentTime()
  
  # DEBUG FOR FRAMES: Return information about the extracted frames
  # return {"message": "Frames extracted", "frames": frames}
  
  # Optionally, clean up by removing the temporary video file
  os.remove(temp_file_path)
  
  # an array that converts the files to File type
  convertedFiles = convertToFile(temp_frame_path)
  
  print(f'Uploading {len(convertedFiles)} files.')
  getCurrentTime()
  
  uploadedFiles = uploadToGeminiFileAPI(convertedFiles)
  
  print(f"Completed file uploads! Uploaded {len(uploadedFiles)} files")
  getCurrentTime()

  # clean up temp frame path
  shutil.rmtree(temp_frame_path)

  # Create the prompt. {timestamp: <given_timestamp>, action: <vibrate, hot, cold, none>, body_part: {chest, left_hand, right_hand, none}}
  prompt = """You are going to be given frames of a video. You are going to return only an array with items that follow this JSON format and the given properties in the type string. {timestamp: <timestamp_of_when_action_occured in minutes:seconds format>, action: <impact, hot>, body_part: <chest, left_hand, right_hand>}.
  
  To tell what action you should choose, in each frame pay attention to if the given surroundings are physically hot. For example, a surrounding of flames and fire will give off high temperatures, and in such is deemed to be hot. Characters can also touch hot items, such as boiling water, a hot plate, and a camp fire. Pay attention to what body part of the character touches that item as it will be returned as an item in json format. An example of what should be returned is: if there is a large evident camp fire in the video and the character puts their right hand into the fire from the time stamp of 00:05 to 00:8 the array that should be sent over is [{timestamp: 00:05, action: hot, body_part: right_hand}, {timestamp: 00:06, action: hot, body_part: right_hand}, {timestamp: 00:07, action: hot, body_part: right_hand}, {timestamp: 00:08, action: hot, body_part: right_hand}] 
  
  Another way to tell which action you should choose is to see if any physical impact (it can be a punch, kick, push, gun shot, sword/weapon clash, or any movement enacted on the character that causes them to shift/move) has effected the character(s) in the frame. Generally, two characters fighting on screen will result in the action: impact. Pay attention to which body part the impact happens on, if the impact was made with the left_hand, the body part is the left hand, if it was made with the right_hand the body part if the right hand, if one is hit in the chest then the body part is the chest. An example of what should be returned if the character punches someone with their left hand and it hits/makes contact the opponent from time stamp of 01:04 to 01:06 the array that should be returned is [{timestamp: 01:04, action: impact, body_part: left_hand}, {timestamp: 01:05, action: impact, body_part: left_hand}, {timestamp: 01:06, action: impact, body_part: left_hand}] this only happens when there is contact made. 

  """

  # Set the model to Gemini 1.5 Pro.
  model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

  # Make the LLM request.
  request = make_request(prompt, uploadedFiles)
  response = model.generate_content(request, request_options={"timeout": 600})
  
  # Strip the non-JSON parts
  json_string = response.text.strip('```json\n').strip('```')
        
  print(json_string)
  
  data = json.loads(json_string)
  
  
  
  return data

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # add the client to the clients dictionary
    global current_client_id
    clients[current_client_id] = websocket
    current_client_id += 1
    try:
      while True:
        data = await websocket.receive_text()
        # await websocket.send_text(f"Message text was: {data}")
        # broadcast the message to all clients (will be the bluetooth client)
        for client_id, client in clients.items():
            # just ignore sending to closed clients
            try:
              await client.send_text(data)
            except Exception as e:
              print(f"Error sending to client {client_id}: {e}")
              
    except WebSocketDisconnect:
      await websocket.close()
      # remove the client from the clients dictionary
      for client_id, client in clients.items():
        if client == websocket:
          del clients[client_id]
      print("Client disconnected")

if __name__ == "__main__":
  uvicorn.run(app, host="127.0.0.1", port=5000)