import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import SubmitTicket from './components/tickets/SubmitTicket';
import ViewReports from './components/reports/ViewReports';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarPinned, setIsSidebarPinned] = useState(true);
  const [activeTab, setActiveTab] = useState('submit');

  // Sidebar collapse/expand logic
  const handleSidebarToggle = () => {
    if (isSidebarCollapsed) {
      setIsSidebarCollapsed(false);
      setIsSidebarOpen(true);
    } else if (isSidebarOpen) {
      setIsSidebarCollapsed(true);
      setIsSidebarOpen(false);
    } else {
      setIsSidebarOpen(true);
    }
  };

  // Pin logic
  const handleSidebarPin = () => setIsSidebarPinned((p) => !p);

  // Tab data with badges
  const tabs = [
    { id: 'submit', label: 'Submit Ticket', icon: '🎫', badge: 0 },
    { id: 'reports', label: 'View Reports', icon: '📊', badge: 3 },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={handleSidebarToggle}
      />
      <div className="flex pt-16"> {/* Added pt-16 for header spacing */}
        <AnimatePresence mode="wait">
          {(isSidebarOpen || isSidebarCollapsed) && (
            <Sidebar
              collapsed={isSidebarCollapsed}
              onCollapseToggle={handleSidebarToggle}
              pinned={isSidebarPinned}
              onPinToggle={handleSidebarPin}
            />
          )}
        </AnimatePresence>
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {/* Enhanced Tab Navigation */}
            <div className="mb-6 border-b border-gray-200 relative z-10">
              <nav className="flex space-x-8 relative">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`relative pb-4 px-1 font-medium text-sm transition-colors duration-200 ${
                      activeTab === tab.id
                        ? 'text-accent'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    aria-label={tab.label}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{tab.icon}</span>
                      <span>{tab.label}</span>
                      {tab.badge > 0 && (
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-accent rounded-full"
                        >
                          {tab.badge}
                        </motion.span>
                      )}
                    </div>
                  </button>
                ))}
                {/* Animated underline */}
                <motion.div
                  className="absolute bottom-0 h-0.5 bg-accent"
                  initial={false}
                  animate={{
                    x: activeTab === 'submit' ? 0 : 120,
                    width: activeTab === 'submit' ? 100 : 110,
                  }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              </nav>
            </div>

            {/* Tab Content with Enhanced Animations */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{
                  duration: 0.3,
                  type: 'spring',
                  stiffness: 300,
                  damping: 30
                }}
              >
                {activeTab === 'submit' ? <SubmitTicket /> : <ViewReports />}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
