import { Route, Routes } from 'react-router-dom';
import { WelcomePage } from './pages/WelcomePage';
import { QuestionPage } from './pages/QuestionPage';
import { ResultsPage } from './pages/ResultsPage';
import { WagtailProvider } from './context/WagtailContext';

export default function App() {
  return (
    <WagtailProvider>
      <main role="main" id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route path="/resultats" element={<ResultsPage />} />
          <Route path="/:questionId" element={<QuestionPage />} />
        </Routes>
      </main>
    </WagtailProvider>
  );
}
