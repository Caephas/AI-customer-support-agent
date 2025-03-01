import axios from "axios";

const API_URL = "http://localhost:8000";

export const sendMessage = async (message: string) => {
  try {
    const response = await axios.post(`${API_URL}/chat`, { message });
    return response.data.reply;
  } catch (error) {
    console.error("Error fetching chatbot response:", error);
    return "Sorry, something went wrong!";
  }
};