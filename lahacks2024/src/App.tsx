import DragDrop from "./components/DragDrop"

function App() {
  return (
    <div className='bg-gradient-to-t from-slate-900 to-slate-700 w-screen h-screen flex justify-center items-center'>
      <div className="text-center p-5">
        <h1 className="bg-gradient-to-r from-yellow-50 to-amber-50 bg-clip-text text-transparent font-bold text-8xl m-7">Haptic Definition</h1>
        <div className="mt-5 mb-10">  {/* Increased bottom margin */}
          <h2 className="bg-gradient-to-r from-yellow-50 to-amber-50 bg-clip-text text-transparent text-3xl p-0.5">Drag and Drop MP4 Files</h2>
        </div>
        <div>
          <DragDrop />
        </div>
      </div>
    </div>
  )
}

export default App