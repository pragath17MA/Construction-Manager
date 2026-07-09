import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import ProjectsList from './pages/ProjectsList';
import CreateProject from './pages/CreateProject';
import EditProject from './pages/EditProject';
import ProjectDetails from './pages/ProjectDetails';
import BudgetDashboard from './pages/BudgetDashboard';
import GenerateEstimate from './pages/GenerateEstimate';
import MaterialsDashboard from './pages/MaterialsDashboard';
import WorkersDashboard from './pages/WorkersDashboard';
import RiskDashboard from './pages/RiskDashboard';
import ProgressDashboard from './pages/ProgressDashboard';
import DocumentDashboard from './pages/DocumentDashboard';
import InvoiceDashboard from './pages/InvoiceDashboard';
import ImageAnalysisDashboard from './pages/ImageAnalysisDashboard';
import VoiceDashboard from './pages/VoiceDashboard';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import ReportCenter from './pages/ReportCenter';
import AIChat from './pages/AIChat';


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected Routes wrapped in Layout shell */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProjectsList />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/create"
            element={
              <ProtectedRoute>
                <Layout>
                  <CreateProject />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProjectDetails />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id/edit"
            element={
              <ProtectedRoute>
                <Layout>
                  <EditProject />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/budget"
            element={
              <ProtectedRoute>
                <Layout>
                  <BudgetDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/budget/new"
            element={
              <ProtectedRoute>
                <Layout>
                  <GenerateEstimate />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/materials"
            element={
              <ProtectedRoute>
                <Layout>
                  <MaterialsDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/workers"
            element={
              <ProtectedRoute>
                <Layout>
                  <WorkersDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/risk"
            element={
              <ProtectedRoute>
                <Layout>
                  <RiskDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/progress"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProgressDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/documents"
            element={
              <ProtectedRoute>
                <Layout>
                  <DocumentDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/invoices"
            element={
              <ProtectedRoute>
                <Layout>
                  <InvoiceDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/image-analysis"
            element={
              <ProtectedRoute>
                <Layout>
                  <ImageAnalysisDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/voice"
            element={
              <ProtectedRoute>
                <Layout>
                  <VoiceDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/executive-dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <ExecutiveDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/report-center"
            element={
              <ProtectedRoute>
                <Layout>
                  <ReportCenter />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <Layout>
                  <AIChat />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Fallback route redirection */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
