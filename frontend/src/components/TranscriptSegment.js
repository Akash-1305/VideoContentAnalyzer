import React from "react";

function TranscriptSegment({ number, text }) {
  return (
    <li>
      <strong>{number}:</strong> {text}
    </li>
  );
}

export default TranscriptSegment;
