/* Ambient declarations for @mediapipe/tasks-vision.
   The real package is a runtime dependency (npm install on a dev machine);
   these declarations exist so typecheck passes in environments where it is
   not installed. When the package IS installed, its own types win. */

declare module "@mediapipe/tasks-vision" {
  export interface MPBox {
    originX: number;
    originY: number;
    width: number;
    height: number;
  }
  export interface Category {
    categoryName: string;
    score: number;
  }
  export interface Detection {
    boundingBox: MPBox;
    categories: Category[];
  }
  export interface DetectionResult {
    detections: Detection[];
  }
  export interface HandLandmark {
    x: number;
    y: number;
    z: number;
  }
  export interface HandLandmarkerResult {
    landmarks: HandLandmark[][];
    handedness: { categoryName: string }[][];
  }
  export interface BaseOptions {
    modelAssetPath: string;
    delegate?: "CPU" | "GPU";
  }
  export class FilesetResolver {
    static forVisionTasks(wasmPath: string): Promise<unknown>;
  }
  export class HandLandmarker {
    static createFromOptions(fileset: unknown, opts: {
      baseOptions: BaseOptions;
      numHands?: number;
      runningMode: "VIDEO";
    }): Promise<HandLandmarker>;
    detectForVideo(video: HTMLVideoElement | HTMLCanvasElement, nowMs: number): HandLandmarkerResult;
    close(): void;
  }
  export class ObjectDetector {
    static createFromOptions(fileset: unknown, opts: {
      baseOptions: BaseOptions;
      maxResults?: number;
      scoreThreshold?: number;
      runningMode: "VIDEO";
    }): Promise<ObjectDetector>;
    detectForVideo(video: HTMLVideoElement | HTMLCanvasElement, nowMs: number): DetectionResult;
    close(): void;
  }
}
