import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon, HardHat } from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="p-2 bg-brand-600/10 text-brand-400 rounded-lg border border-brand-500/20">
                <HardHat className="w-6 h-6" />
              </div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                APEX<span className="text-brand-400">Build</span>
              </span>
            </Link>
            
            {user && (
              <nav className="hidden md:flex space-x-6">
                <Link to="/dashboard" className="text-sm font-semibold text-slate-350 hover:text-white transition-colors">Dashboard</Link>
                <Link to="/projects" className="text-sm font-semibold text-slate-350 hover:text-white transition-colors">Projects</Link>
                <Link to="/executive-dashboard" className="text-sm font-semibold text-slate-350 hover:text-white transition-colors">Executive Stats</Link>
                <Link to="/report-center" className="text-sm font-semibold text-slate-350 hover:text-white transition-colors">Report Center</Link>
                <Link to="/chat" className="text-sm font-semibold text-slate-350 hover:text-white transition-colors">AI Chat</Link>
              </nav>
            )}
          </div>

          {user && (
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                  <UserIcon className="w-5 h-5" />
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-semibold text-slate-200 leading-tight">{user.full_name}</p>
                  <p className="text-xs text-brand-400 font-medium leading-none mt-1">{user.role}</p>
                </div>
              </div>

              <button
                onClick={logout}
                className="inline-flex items-center justify-center p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all duration-200"
                title="Log Out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;
