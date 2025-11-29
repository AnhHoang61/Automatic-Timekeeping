// // src/pages/FaceAttendance.jsx
// import React, { useRef, useState } from "react";
// import faceApi from "../api/faceApi";
// import "./FaceAttendance.css"; // nếu có

// export default function FaceAttendance() {
//   const videoRef = useRef(null);
//   const canvasRef = useRef(null);

//   const [previewUrl, setPreviewUrl] = useState(null);
//   const [isCameraOn, setIsCameraOn] = useState(false);
//   const [loading, setLoading] = useState(false);
//   const [result, setResult] = useState(null);

//   // Bật camera
//   const handleStartCamera = async () => {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({
//         video: true,
//         audio: false,
//       });
//          if (videoRef.current) {
//       videoRef.current.srcObject = stream;
//     }
//     } catch (err) {
//       console.error("Không mở được camera:", err);
//       alert("Không mở được camera. Kiểm tra quyền truy cập camera.");
//     }
//   };

//   // Tắt camera (nếu cần)
//   const stopCamera = () => {
//     const stream = videoRef.current?.srcObject;
//     if (stream) {
//       stream.getTracks().forEach((t) => t.stop());
//       videoRef.current.srcObject = null;
//     }
//     setIsCameraOn(false);
//   };

//   // Chụp ảnh từ video -> lưu preview và trả về Blob
//   const captureFrame = () =>
//     new Promise((resolve, reject) => {
//       const video = videoRef.current;
//       const canvas = canvasRef.current;
//       if (!video || !canvas) return reject("Không có video/canvas");

//       const w = video.videoWidth || 640;
//       const h = video.videoHeight || 480;

//       canvas.width = w;
//       canvas.height = h;

//       const ctx = canvas.getContext("2d");
//       ctx.drawImage(video, 0, 0, w, h);

//       canvas.toBlob(
//         (blob) => {
//           if (!blob) return reject("Không tạo được blob từ canvas");

//           // tạo preview để hiển thị
//           const url = URL.createObjectURL(blob);
//           setPreviewUrl(url);
//           resolve(blob);
//         },
//         "image/jpeg",
//         0.9
//       );
//     });

//   // Chụp ảnh (demo) – chỉ cập nhật preview, chưa gửi API
//   const handleCaptureDemo = async () => {
//     try {
//       await captureFrame();
//     } catch (err) {
//       console.error(err);
//       alert("Chụp ảnh thất bại");
//     }
//   };

//   // Check-in bằng mặt
//   const handleFaceCheckin = async () => {
//     try {
//       setLoading(true);
//       setResult(null);

//       const blob = await captureFrame();

//       const res = await faceApi.checkin(blob);
//       setResult(res.data);
//     } catch (err) {
//       console.error("Face checkin error:", err);
//       if (err.response) {
//         alert("Lỗi check-in: " + JSON.stringify(err.response.data));
//       } else {
//         alert("Lỗi check-in, xem console");
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Check-out bằng mặt
//   const handleFaceCheckout = async () => {
//     try {
//       setLoading(true);
//       setResult(null);

//       const blob = await captureFrame();

//       const res = await faceApi.checkout(blob);
//       setResult(res.data);
//     } catch (err) {
//       console.error("Face checkout error:", err);
//       if (err.response) {
//         alert("Lỗi check-out: " + JSON.stringify(err.response.data));
//       } else {
//         alert("Lỗi check-out, xem console");
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="face-attendance-page">
//       <h1 className="face-title">Chấm công bằng khuôn mặt</h1>

//       <div className="face-layout">
//         {/* Khung camera + preview */}
//         <div className="face-left">
//           <div className="camera-box">
//             {isCameraOn ? (
//               <video
//                 ref={videoRef}
//                 autoPlay
//                 playsInline
//                 className={`camera-video ${isCameraOn ? "show" : "hide"}`}
//               />
//             ) : (
//               <div className="camera-placeholder">
//                 Khung camera (demo) – ảnh sẽ hiển thị sau khi chụp.
//               </div>
//             )}

//             {/* Canvas ẩn dùng để capture */}
//             <canvas ref={canvasRef} style={{ display: "none" }} />

//             {/* Ảnh preview (nếu có) */}
//             {previewUrl && (
//               <img src={previewUrl} alt="Preview" className="preview-image" />
//             )}
//           </div>

//           <div className="face-actions">
//             <button onClick={handleStartCamera} disabled={isCameraOn}>
//               Bật camera
//             </button>
//             <button onClick={stopCamera} disabled={!isCameraOn}>
//               Tắt camera
//             </button>
//             <button onClick={handleCaptureDemo} disabled={!isCameraOn}>
//               Chụp ảnh (demo)
//             </button>
//             <button
//               onClick={handleFaceCheckin}
//               disabled={!isCameraOn || loading}
//             >
//               ✅ Check-in bằng mặt
//             </button>
//             <button
//               onClick={handleFaceCheckout}
//               disabled={!isCameraOn || loading}
//             >
//               🧾 Check-out bằng mặt
//             </button>
//           </div>
//         </div>

//         {/* Kết quả trả về từ API */}
//         <div className="face-right">
//           <h2>Kết quả chấm công</h2>
//           {loading && <p>Đang xử lý khuôn mặt...</p>}
//           {!loading && !result && <p>Chưa có kết quả.</p>}
//           {!loading && result && (
//             <pre className="result-box">
// {JSON.stringify(result, null, 2)}
//             </pre>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }
