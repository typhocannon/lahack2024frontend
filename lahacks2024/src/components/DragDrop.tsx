import React, { useState } from "react";
import { FileUploader } from "react-drag-drop-files";

const fileTypes: string[] = ["MP4"];

function DragDrop() {
  const [file, setFile] = useState<File | null>(null);

  const handleChange = (file: File) => {
    setFile(file);
  };

  return (
    <div>
      <FileUploader handleChange={handleChange} name="file" types={fileTypes} />
      {file && (
        <div>
          <h2>Uploaded Video:</h2>
          <video src={URL.createObjectURL(file)} controls width="400" height="300"></video>
        </div>
      )}
    </div>
  );
}

export default DragDrop;
