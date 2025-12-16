'use client';

import React, { useEffect, useState } from 'react';

interface MathCaptchaProps {
  onVerify: (isValid: boolean) => void;
  className?: string;
}

/**
 * Simple math captcha to prevent bot submissions
 * Generates random addition problem (1-10 + 1-10)
 * No external dependencies, GDPR-friendly
 */
export const MathCaptcha: React.FC<MathCaptchaProps> = ({ onVerify, className = '' }) => {
  const [num1, setNum1] = useState(0);
  const [num2, setNum2] = useState(0);
  const [answer, setAnswer] = useState('');
  const [correctAnswer, setCorrectAnswer] = useState(0);
  const [touched, setTouched] = useState(false);

  const generateNewQuestion = () => {
    const n1 = Math.floor(Math.random() * 10) + 1;
    const n2 = Math.floor(Math.random() * 10) + 1;
    setNum1(n1);
    setNum2(n2);
    setCorrectAnswer(n1 + n2);
    setAnswer('');
    setTouched(false);
    onVerify(false);
  };

  useEffect(() => {
    // Generate new math question on mount
    generateNewQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (value: string) => {
    setAnswer(value);
    setTouched(true);
    const isCorrect = parseInt(value) === correctAnswer;
    onVerify(isCorrect);
  };

  const isCorrect = touched && parseInt(answer) === correctAnswer;
  const isIncorrect = touched && answer !== '' && parseInt(answer) !== correctAnswer;

  return (
    <div className={`bg-light rounded border p-3 ${className}`}>
      <label className="form-label mb-2">
        <strong>🤖 Verify you&apos;re human:</strong>
      </label>
      <div className="flex items-center gap-2">
        <div className="flex-grow-1">
          <div className="input-group">
            <span className="input-group-text bg-white">
              What is{' '}
              <strong className="mx-1">
                {num1} + {num2}
              </strong>
              ?
            </span>
            <input
              type="number"
              className={`form-control ${isCorrect ? 'is-valid' : ''} ${isIncorrect ? 'is-invalid' : ''}`}
              value={answer}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Enter answer"
              required
              aria-label="Math captcha answer"
            />
          </div>
          {isCorrect && (
            <div className="text-green-600 text-sm font-medium mt-1">✓ Correct! You&apos;re verified.</div>
          )}
          {isIncorrect && (
            <div className="text-red-600 text-sm font-medium mt-1">✗ Incorrect answer. Please try again.</div>
          )}
        </div>
        <button
          type="button"
          className="flex-shrink-0 px-3 py-2 border-2 border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 hover:border-gray-400 transition-all duration-200"
          onClick={generateNewQuestion}
          title="Generate new question"
          aria-label="Generate new question"
        >
          🔄
        </button>
      </div>
      <small className="text-gray-500 text-sm block mt-1">
        This helps us prevent automated spam bookings.
      </small>
    </div>
  );
};

export default MathCaptcha;
