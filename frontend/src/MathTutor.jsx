import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { RadioGroup, RadioGroupItem } from "./components/ui/radio-group";
import { Label } from "./components/ui/label";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Loader2 } from "lucide-react";
import { useToast } from "./components/ui/use-toast";

const MathTutor = () => {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const topics = [
    { value: "algebra", label: "Algebra" },
    { value: "geometry", label: "Geometry" },
    { value: "trigonometry", label: "Trigonometry" },
    { value: "calculus", label: "Calculus" },
    { value: "statistics", label: "Statistics" },
  ];

  const difficulties = [
    { value: "beginner", label: "Beginner" },
    { value: "intermediate", label: "Intermediate" },
    { value: "advanced", label: "Advanced" },
  ];

  const handleError = (error, customMessage) => {
    console.error(error);
    toast({
      title: "Error",
      description: customMessage,
      variant: "destructive",
    });
  };

  const fetchQuestion = async () => {
    if (!topic || !difficulty) {
      toast({
        title: "Invalid Input",
        description: "Please select both topic and difficulty",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_BASE_URL}/questions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic, difficulty }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Validate response data
      if (!data.id || !data.question_text || !Array.isArray(data.options)) {
        throw new Error("Invalid question format received");
      }

      setQuestion(data);
      setSelectedAnswer("");
      setFeedback(null);
    } catch (error) {
      handleError(error, "Failed to fetch question. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!question?.id || !selectedAnswer) {
      toast({
        title: "Invalid Submission",
        description: "Please select an answer before submitting",
        variant: "destructive",
      });
      return;
    }
  
    try {
      setLoading(true); // Keep loading state true
  
      const response = await fetch("http://localhost:8000/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: question.id,
          selected_answer: selectedAnswer,
        }),
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
  
      // Validate feedback data
      if (typeof data.is_correct !== "boolean" || !Array.isArray(data.solution_steps)) {
        throw new Error("Invalid feedback format received");
      }
  
      // Introduce a 5-second delay before showing feedback
      setTimeout(() => {
        setFeedback(data);
        setLoading(false); // Stop loading after delay
      }, 5000);
    } catch (error) {
      handleError(error, "Failed to submit answer. Please try again.");
      setLoading(false); // Stop loading immediately on error
    }
  };
  

  return (
    <div className="container mx-auto p-4 max-w-3xl">
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Interactive Math Tutor</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <Label>Topic</Label>
              <Select value={topic} onValueChange={setTopic}>
                <SelectTrigger>
                  <SelectValue placeholder="Select topic" />
                </SelectTrigger>
                <SelectContent>
                  {topics.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Difficulty</Label>
              <Select value={difficulty} onValueChange={setDifficulty}>
                <SelectTrigger>
                  <SelectValue placeholder="Select difficulty" />
                </SelectTrigger>
                <SelectContent>
                  {difficulties.map((d) => (
                    <SelectItem key={d.value} value={d.value}>
                      {d.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            onClick={fetchQuestion}
            disabled={!topic || !difficulty || loading}
            className="w-full"
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              "Get Question"
            )}
          </Button>
        </CardContent>
      </Card>

      {question && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Question</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg mb-6">{question.question_text}</p>
            <RadioGroup
              value={selectedAnswer}
              onValueChange={setSelectedAnswer}
              className="space-y-4"
            >
              {question.options.map((option, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <RadioGroupItem value={option.text} id={`option-${index}`} />
                  <Label htmlFor={`option-${index}`}>{option.text}</Label>
                </div>
              ))}
            </RadioGroup>
            <Button
              onClick={submitAnswer}
              disabled={!selectedAnswer || loading}
              className="w-full mt-6"
            >
              {loading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                "Submit Answer"
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {feedback && (
        <Card>
          <CardHeader>
            <CardTitle>
              {feedback.is_correct ? "Correct! 🎉" : "Not quite right"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert className="mb-4">
              <AlertDescription>{feedback.explanation}</AlertDescription>
            </Alert>
            <div className="space-y-4">
              <h3 className="font-semibold">Solution Steps:</h3>
              <ol className="list-decimal list-inside space-y-2">
                {feedback.solution_steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
            {/* <div className="mt-6 p-4 bg-slate-50 rounded-lg">
              <h3 className="font-semibold mb-2">Performance Stats:</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-slate-600">Total Attempts</p>
                  <p className="text-lg font-semibold">
                    {feedback.performance_stats.total_attempts}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-600">Correct Answers</p>
                  <p className="text-lg font-semibold">
                    {feedback.performance_stats.correct_attempts}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-600">Success Rate</p>
                  <p className="text-lg font-semibold">
                    {feedback.performance_stats.success_rate.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div> */}
            <Button onClick={fetchQuestion} className="w-full mt-6">
              Try Another Question
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MathTutor;
