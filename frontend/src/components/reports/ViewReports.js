import React, { useState, useEffect, useMemo } from 'react';
import { useTable, useSortBy, usePagination, useRowSelect } from 'react-table';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronUpIcon, 
  ChevronDownIcon, 
  MagnifyingGlassIcon,
  DocumentArrowDownIcon,
  TrashIcon,
  EyeIcon,
  ChartBarIcon,
  FunnelIcon,
  CalendarIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

function ViewReports() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch data from the escalation-log endpoint
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:2024/escalation-log');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        if (result.success) {
          setData(result.data || []);
        } else {
          throw new Error('Failed to fetch data');
        }
      } catch (error) {
        console.error('Error fetching escalation log:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Define columns based on CSV fields
  const columns = useMemo(
    () => [
      {
        Header: 'Select',
        accessor: 'select',
        Cell: ({ row }) => (
          <input
            type="checkbox"
            checked={row.isSelected}
            onChange={() => row.toggleRowSelected()}
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-0"
          />
        ),
      },
      {
        Header: 'Timestamp',
        accessor: 'timestamp',
        Cell: ({ value }) => (
          <div className="flex items-center space-x-2">
            <ClockIcon className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600 font-medium">
              {new Date(value).toLocaleString()}
            </span>
          </div>
        ),
      },
      {
        Header: 'Ticket ID',
        accessor: 'ticket_id',
        Cell: ({ value }) => (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
            {value}
          </span>
        ),
      },
      {
        Header: 'Subject',
        accessor: 'subject',
        Cell: ({ value }) => (
          <div className="max-w-xs">
            <p className="text-sm font-medium text-gray-900 truncate" title={value}>
              {value}
            </p>
          </div>
        ),
      },
      {
        Header: 'Description',
        accessor: 'description',
        Cell: ({ value }) => (
          <div className="max-w-xs">
            <p className="text-sm text-gray-600 truncate" title={value}>
              {value}
            </p>
          </div>
        ),
      },
      {
        Header: 'Category',
        accessor: 'category',
        Cell: ({ value }) => (
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            value === 'general' ? 'bg-blue-100 text-blue-800' :
            value === 'technical' ? 'bg-emerald-100 text-emerald-800' :
            value === 'billing' ? 'bg-amber-100 text-amber-800' :
            value === 'security' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {value}
          </span>
        ),
      },
      {
        Header: 'Confidence',
        accessor: 'classification_confidence',
        Cell: ({ value }) => (
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${parseFloat(value) * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-600">
              {(parseFloat(value) * 100).toFixed(0)}%
            </span>
          </div>
        ),
      },
      {
        Header: 'Drafts',
        accessor: 'num_drafts',
        Cell: ({ value }) => (
          <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800">
            {value}
          </span>
        ),
      },
      {
        Header: 'Reviews',
        accessor: 'num_reviews',
        Cell: ({ value }) => (
          <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-cyan-100 text-cyan-800">
            {value}
          </span>
        ),
      },
      {
        Header: 'Review Score',
        accessor: 'final_review_score',
        Cell: ({ value }) => {
          const score = parseFloat(value) * 100;
          return (
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    score >= 80 ? 'bg-gradient-to-r from-green-400 to-emerald-500' :
                    score >= 60 ? 'bg-gradient-to-r from-yellow-400 to-orange-500' :
                    'bg-gradient-to-r from-red-400 to-pink-500'
                  }`}
                  style={{ width: `${score}%` }}
                />
              </div>
              <span className={`text-xs font-medium ${
                score >= 80 ? 'text-green-600' :
                score >= 60 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {score.toFixed(0)}%
              </span>
            </div>
          );
        },
      },
      {
        Header: 'Escalation Reason',
        accessor: 'escalation_reason',
        Cell: ({ value }) => (
          <div className="max-w-xs">
            <p className="text-sm text-gray-600 truncate" title={value}>
              {value}
            </p>
          </div>
        ),
      },
      {
        Header: 'Failed Drafts',
        accessor: 'failed_drafts',
        Cell: ({ value }) => (
          <div className="max-w-xs">
            <p className="text-sm text-red-600 truncate" title={value}>
              {value}
            </p>
          </div>
        ),
      },
      {
        Header: 'Reviewer Feedback',
        accessor: 'reviewer_feedback',
        Cell: ({ value }) => (
          <div className="max-w-xs">
            <p className="text-sm text-gray-600 truncate" title={value}>
              {value}
            </p>
          </div>
        ),
      },
      {
        Header: 'Actions',
        accessor: 'actions',
        Cell: ({ row }) => (
          <div className="flex items-center space-x-1">
            <button
              onClick={() => handleView(row.original)}
              className="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
              title="View Details"
            >
              <EyeIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleDelete(row.original)}
              className="p-1.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
              title="Delete"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
        ),
      },
    ],
    []
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    canPreviousPage,
    canNextPage,
    pageOptions,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize },
  } = useTable(
    {
      columns,
      data,
      initialState: { pageIndex: 0, pageSize: 10 },
    },
    useSortBy,
    usePagination,
    useRowSelect
  );

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchTerm) return data;
    
    return data.filter(item =>
      Object.values(item).some(value =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  const handleView = (row) => {
    console.log('View details for:', row);
    // Implement view functionality
  };

  const handleDelete = (row) => {
    console.log('Delete:', row);
    // Implement delete functionality
  };

  const exportCSV = () => {
    const headers = columns
      .filter(col => col.accessor !== 'select' && col.accessor !== 'actions')
      .map(col => col.Header)
      .join(',');
    
    const csvData = filteredData.map(row => 
      columns
        .filter(col => col.accessor !== 'select' && col.accessor !== 'actions')
        .map(col => {
          const value = row[col.accessor];
          return `"${String(value).replace(/"/g, '""')}"`;
        })
        .join(',')
    ).join('\n');
    
    const csv = `${headers}\n${csvData}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'escalation_log.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading escalation data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 text-lg font-medium mb-2">Error loading data</div>
        <div className="text-gray-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Escalation Log</h2>
              <p className="text-gray-600">View and manage escalation records with detailed analytics</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={exportCSV}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 shadow-sm"
            >
              <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Search */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search records by any field..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200"
        />
      </div>

      {/* Enhanced Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table {...getTableProps()} className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
              {headerGroups.map(headerGroup => (
                <tr {...headerGroup.getHeaderGroupProps()}>
                  {headerGroup.headers.map(column => (
                    <th
                      {...column.getHeaderProps(column.getSortByToggleProps())}
                      className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                    >
                      <div className="flex items-center space-x-1">
                        <span>{column.render('Header')}</span>
                        {column.isSorted ? (
                          column.isSortedDesc ? (
                            <ChevronDownIcon className="w-4 h-4 text-indigo-600" />
                          ) : (
                            <ChevronUpIcon className="w-4 h-4 text-indigo-600" />
                          )
                        ) : null}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody {...getTableBodyProps()} className="bg-white divide-y divide-gray-200">
              {page.map(row => {
                prepareRow(row);
                return (
                  <motion.tr
                    {...row.getRowProps()}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 transition-all duration-200"
                  >
                    {row.cells.map(cell => (
                      <td
                        {...cell.getCellProps()}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                      >
                        {cell.render('Cell')}
                      </td>
                    ))}
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Enhanced Pagination */}
        <div className="bg-white px-6 py-4 flex items-center justify-between border-t border-gray-200">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => previousPage()}
              disabled={!canPreviousPage}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => nextPage()}
              disabled={!canNextPage}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div className="flex gap-x-2 items-baseline">
              <span className="text-sm text-gray-700">
                Page <span className="font-medium">{pageIndex + 1}</span> of{' '}
                <span className="font-medium">{pageOptions.length}</span>
              </span>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => previousPage()}
                  disabled={!canPreviousPage}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => nextPage()}
                  disabled={!canNextPage}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Empty State */}
      {filteredData.length === 0 && (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            <ChartBarIcon className="w-full h-full" />
          </div>
          <h3 className="text-sm font-medium text-gray-900 mb-2">No records found</h3>
          <p className="text-sm text-gray-500">Try adjusting your search criteria</p>
        </div>
      )}
    </div>
  );
}

export default ViewReports; 