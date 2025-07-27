import React from 'react';
import { Menu } from '@headlessui/react';
import { motion } from 'framer-motion';
import { Bars3Icon, XMarkIcon, BellIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

function Header({ isSidebarOpen, onToggleSidebar }) {
  return (
    <header className="bg-white shadow-sm h-[60px] fixed w-full top-0 z-50">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left side with hamburger and centered title */}
        <div className="flex items-center flex-1">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 transition-all duration-200"
            aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <motion.div
              animate={{ rotate: isSidebarOpen ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              {isSidebarOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </motion.div>
          </button>
          
          {/* Centered title */}
          <motion.h1 
            className="ml-4 text-xl font-semibold text-primary"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            Support Dashboard
          </motion.h1>
        </div>

        {/* Right side with notifications and user menu */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button 
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 transition-all duration-200 relative group"
            aria-label="Notifications"
          >
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <BellIcon className="w-6 h-6" />
            </motion.div>
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            {/* Notification tooltip */}
            <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
              New notifications
            </span>
          </button>

          {/* User Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 transition-all duration-200 group">
              <motion.div 
                className="w-8 h-8 rounded-full bg-gradient-to-r from-accent to-purple-500 text-white flex items-center justify-center shadow-md"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className="text-sm font-medium">JD</span>
              </motion.div>
              <motion.div
                animate={{ rotate: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Cog6ToothIcon className="w-5 h-5 text-gray-600 group-hover:text-accent transition-colors duration-200" />
              </motion.div>
            </Menu.Button>

            <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 focus:outline-none border border-gray-200">
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Menu.Item>
                  {({ active }) => (
                    <motion.a
                      href="#profile"
                      className={`${
                        active ? 'bg-accent/10 text-accent' : 'text-gray-700'
                      } block px-4 py-2 text-sm transition-colors duration-200`}
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      👤 Your Profile
                    </motion.a>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <motion.a
                      href="#settings"
                      className={`${
                        active ? 'bg-accent/10 text-accent' : 'text-gray-700'
                      } block px-4 py-2 text-sm transition-colors duration-200`}
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      ⚙️ Settings
                    </motion.a>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <motion.a
                      href="#signout"
                      className={`${
                        active ? 'bg-red-50 text-red-600' : 'text-gray-700'
                      } block px-4 py-2 text-sm transition-colors duration-200`}
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      🚪 Sign out
                    </motion.a>
                  )}
                </Menu.Item>
              </motion.div>
            </Menu.Items>
          </Menu>
        </div>
      </div>
    </header>
  );
}

export default Header; 