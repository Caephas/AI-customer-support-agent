import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const sendMessageToBackend = async (
  userMessage: string,
  userId: string,
  token: string
): Promise<string> => {
  try {
    // Send initial request to /chat/query
    const initialRes = await axios.post(
      `${API_BASE_URL}/chat/query`,
      { user_id: userId, message: userMessage },
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        withCredentials: true,
      }
    );
    console.log("Initial API response:", initialRes.data);

    // If the backend returns a task_id, it means it's processing asynchronously.
    if (initialRes.data.task_id) {
      const taskId = initialRes.data.task_id;
      const finalReply = await pollForResult(taskId, token);
      return finalReply;
    } else {
      // Otherwise, it's a cached response
      return initialRes.data.response;
    }
  } catch (error) {
    console.error("Error sending message:", error);
    throw error;
  }
};

const pollForResult = async (
  taskId: string,
  token: string,
  interval = 1000,
  timeout = 30000
): Promise<string> => {
  const startTime = Date.now();

  while (true) {
    const statusRes = await axios.get(`${API_BASE_URL}/chat/query/status/${taskId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("Status response:", statusRes.data);
    if (statusRes.data.status === "completed") {
      // The final AI response is nested: { ..., response: { response: "final reply", ... } }
      return statusRes.data.response.response;
    }
    if (Date.now() - startTime > timeout) {
      throw new Error("Timed out waiting for task completion.");
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
};