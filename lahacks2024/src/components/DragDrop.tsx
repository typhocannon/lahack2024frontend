import { useState } from "react";
import { FileUploader } from "react-drag-drop-files";
import { Button } from "@mui/material";
import axios from "axios";
import { useMemo } from "react";

const fileTypes: string[] = ["MP4"];

function DragDrop() {
  const [mp4file, setFile] = useState<File | null>(null);
  const [currentTime, setCurrentTime] = useState("00:00")
  const [timeStampDict, setTimeStampDict] = useState<[{timestamp: string, action: string, body_part: string}]>([{
    timestamp: "",
    action: "",
    body_part: ""
  }]);
  // const [timeStampDict, setTimeStampDict] = useState<{timestamp: string, action: string, body_part: string}>({
  //   timestamp: "",
  //   action: "",
  //   body_part: ""
  // });

  const handleChange = (mp4file: File) => {
    setFile(mp4file);
  };

  // keeps video from refreshing 
  const videoSrc = useMemo(() => {
    return mp4file ? URL.createObjectURL(mp4file) : "";
  }, [mp4file]);

  const formatTime = (timeInSeconds: number): string => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    const formattedMinutes = minutes.toString().padStart(2, '0');
    const formattedSeconds = seconds.toString().padStart(2, '0');
    return `${formattedMinutes}:${formattedSeconds}`;
  };

  const handleTimeUpdate: React.VideoHTMLAttributes<HTMLVideoElement>['onTimeUpdate'] = (event) => {
    event.stopPropagation();
    if (event.target) {
      const videoElement = event.target as HTMLVideoElement;
      const time = videoElement.currentTime;
      const formattedTime = formatTime(time);
      setCurrentTime(formattedTime);

      // debug showing current time
      console.log(`Current time: ${formattedTime}`);

      // check if the current timestamp is in the action list thing, if so then do something
      for(const item of timeStampDict) {
        if (formattedTime == item.timestamp) {
          console.log("do something")
        }
      }
    }
  };

  const sendFile = async () => {
    if (mp4file) {
      const formData = new FormData();
      formData.append("file_sent", mp4file);
      console.log(Array.from(formData))
      
      const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      try {
        console.log('File uploaded successfully', response.data);

        const newData = response.data;

        console.log(newData)
        setTimeStampDict(newData);

      } catch (error) {
        console.error('Error uploading file', error);
      }
    } else {
      console.log('No file selected');
    }
  }

  return (
    <div className="flex flex-col items-center justify-center m-5">
      <FileUploader handleChange={handleChange} name="file" types={fileTypes} />
      {mp4file && (
        <div className="text-center">
          <h2>View Uploaded Video:</h2>
          <video src={videoSrc} controls width="1000" onTimeUpdate={handleTimeUpdate}></video>
        </div>
      )}
      <div className="m-5">
        <Button onClick={sendFile} className="mt-4" variant="contained" size="large">Submit</Button>
      </div>
    </div>
  );
}

export default DragDrop;
