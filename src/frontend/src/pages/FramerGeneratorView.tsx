import React, { useState, useRef, useEffect } from 'react';

export default function FramerGeneratorView() {
  const [description, setDescription] = useState('');
  const [generatedCode, setGeneratedCode] = useState('// Your Framer component code will appear here');
  const [previewContent, setPreviewContent] = useState('<div>Preview Area</div>');

  const handleGenerate = () => {
    // Simulate API call to generate Framer component code
    if (description.trim()) {
      const simulatedCode = `import * as React from "react"
import { Frame } from "framer"

export function MyFramerComponent() {
  return (
    <Frame
      width={150}
      height={80}
      radius={10}
      background={"#0099FF"}
      color={"#FFFFFF"}
      fontSize={20}
      whileHover={{ scale: 1.1 }}
    >
      {/* You described: "${description}" */}
      Click Me
    </Frame>
  )
}
`;
      setGeneratedCode(simulatedCode);
      setPreviewContent(`
        <iframe
          srcDoc={
            `<html>
              <head>
                <style>
                  body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }
                </style>
              </head>
              <body>
                <div style="
                  width: 150px;
                  height: 80px;
                  border-radius: 10px;
                  background-color: #0099FF;
                  color: #FFFFFF;
                  font-size: 20px;
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                  cursor: pointer;
                ">Click Me</div>
              </body>
            </html>`}
          width="100%" height="300px" style="border:none;">
        </iframe>
      `);
    } else {
      setGeneratedCode('Please enter a description.');
      setPreviewContent('<div>Enter a description to see preview.</div>');
    }
  };

  const handleRefine = () => {
    alert('Refine functionality not implemented yet.');
  };

  const handleSave = () => {
    alert('Save functionality not implemented yet.');
  };

  const handleDeploy = () => {
    alert('Deploy functionality not implemented yet.');
  };

  return (
    <div className="flex flex-col h-full bg-gray-100 rounded-lg shadow-md overflow-hidden">
      <div className="bg-indigo-600 text-white p-4 text-lg font-semibold">Framer Component Generator</div>
      <div className="p-4 flex-grow">
        {/* Top Panel: Description Input and Action Buttons */}
        <div className="mb-4">
          <textarea
            className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows={4}
            placeholder="Describe the Framer component you want to generate (e.g., 'a spinning cube with red background and 'Hello' text')..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div className="mt-2 flex space-x-2">
            <button
              className="px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              onClick={handleGenerate}
            >
              Generate Component
            </button>
            <button
              className="px-5 py-2 bg-gray-400 text-white rounded-lg hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500"
              onClick={handleRefine}
            >
              Refine
            </button>
          </div>
        </div>

        {/* Middle Panel: Code and Preview Areas */}
        <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4 flex-grow">
          <div className="flex-1 bg-white p-4 rounded-lg shadow-md">
            <h3 className="text-md font-semibold mb-2">Generated Code</h3>
            <textarea
              readOnly
              className="w-full h-full p-3 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm resize-none focus:outline-none"
              value={generatedCode}
            />
          </div>
          <div className="flex-1 bg-white p-4 rounded-lg shadow-md">
            <h3 className="text-md font-semibold mb-2">Preview</h3>
            <div className="w-full h-full border border-gray-300 rounded-lg flex items-center justify-center overflow-hidden">
              <div dangerouslySetInnerHTML={{ __html: previewContent }} />
            </div>
          </div>
        </div>
      </div>
      {/* Bottom Panel: Action Buttons */}
      <div className="p-4 bg-white border-t border-gray-200 flex justify-end space-x-2">
        <button
          className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
          onClick={handleSave}
        >
          Save Component
        </button>
        <button
          className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
          onClick={handleDeploy}
        >
          Deploy
        </button>
      </div>
    </div>
  );
}
