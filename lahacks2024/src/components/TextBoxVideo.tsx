import React, { useState } from "react";
import { TextField } from "@mui/material";
import ytdl from 'ytdl-core';

function TextBoxVideo() {
  const [urlLink, setUrlLink] = useState<string>("");
  const [downloadedBlob, setDownloadedBlob] = useState<Blob | null>(null);

  const handleTextInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    // Regular expression to match common video file extensions and YouTube/Vimeo URLs
    const videoRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})$/;

    if (videoRegex.test(value)) {
      setUrlLink(value);
      // Call handleDownload directly with the updated value
      handleDownload(value);
    } else {
      setUrlLink(""); // Clear the input if it's not a valid video link
    }
  };

  const handleDownload = async (videoUrl: string) => {
    try {
      // Check if the link is a valid YouTube link
      if (!ytdl.validateURL(videoUrl)) {
        throw new Error('Invalid YouTube link');
      }

      // Get video info
      const info = await ytdl.getInfo(videoUrl);

      // Get the highest quality video format
      const format = ytdl.chooseFormat(info.formats, { quality: 'highestvideo' });

      // Download the video
      const videoReadableStream = ytdl.downloadFromInfo(info, { format: format });
      const chunks: Uint8Array[] = [];

      videoReadableStream.on('data', (chunk: Uint8Array) => {
        chunks.push(chunk);
      });

      videoReadableStream.on('end', () => {
        const blob = new Blob(chunks, { type: 'video/mp4' });
        setDownloadedBlob(blob);
      });
    } catch (error) {
      console.error('Error downloading video:', error);
    }
  };

  return (
    <div>
      <TextField
        id="outlined-basic"
        label="Video URL"
        variant="outlined"
        value={urlLink}
        onChange={handleTextInput}
      />
      {downloadedBlob && (
        <div>
          <h2>Uploaded Video:</h2>
          <video src={URL.createObjectURL(downloadedBlob)} controls width="400" height="300"></video>
        </div>
      )}
    </div>
  );
}

export default TextBoxVideo;
