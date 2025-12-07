/** Main App component with routing and theme support */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, QuestionProvider } from './contexts';
import { MainLayout } from './components/layout';
import { ChatPage, SchemaExplorerPage, HistoryPage, SettingsPage } from './pages';

function App() {
    return (
        <ThemeProvider>
            <QuestionProvider>
                <BrowserRouter>
                    <MainLayout>
                        <Routes>
                            <Route path="/" element={<ChatPage />} />
                            <Route path="/schema" element={<SchemaExplorerPage />} />
                            <Route path="/history" element={<HistoryPage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                        </Routes>
                    </MainLayout>
                </BrowserRouter>
            </QuestionProvider>
        </ThemeProvider>
    );
}

export default App;
