import { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, ShieldAlert, Clock, ChevronRight, ArrowLeft, Upload, X } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = 'http://localhost:8000/api/payments';

type PaymentSummary = {
  id: number;
  customer_name: string;
  amount: number;
  status: string;
  decision: string;
  created_at: string;
};

type PaymentDetail = {
  id: number;
  image_path: string;
  customer: { name: string; phone: string };
  order: { id: number; expected_amount: number; expected_account: string };
  submitted: { amount: number; account_no: string; reference: string; date: string };
  verification: {
    decision: string;
    internal_reason: string;
    customer_message: string;
    confidence_score: number;
    evidence_json: string;
  };
};

function StatusBadge({ decision }: { decision: string }) {
  if (decision === 'APPROVED') {
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><ShieldCheck className="w-3 h-3 mr-1" /> Approved</span>;
  }
  if (decision === 'REJECTED') {
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><ShieldAlert className="w-3 h-3 mr-1" /> Rejected</span>;
  }
  return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"><Clock className="w-3 h-3 mr-1" /> Needs Verification</span>;
}

function App() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-blue-600" /> PayGuard
        </h1>
      </header>
      
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {selectedId ? (
          <DetailView id={selectedId} onBack={() => setSelectedId(null)} />
        ) : (
          <Dashboard onSelect={setSelectedId} />
        )}
      </main>
    </div>
  );
}

function Dashboard({ onSelect }: { onSelect: (id: number) => void }) {
  const [payments, setPayments] = useState<PaymentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  const fetchPayments = () => {
    setLoading(true);
    axios.get(API_BASE).then(res => {
      setPayments(res.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  if (loading && payments.length === 0) return <div className="text-center py-10">Loading payments...</div>;

  return (
    <>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Payment Submissions</h3>
            <p className="mt-1 text-sm text-gray-500">Review WhatsApp payment receipts submitted by customers.</p>
          </div>
          <button 
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 bg-blue-600 text-white hover:bg-blue-700 h-9 px-4 py-2"
          >
            <Upload className="w-4 h-4 mr-2" /> Upload Slip
          </button>
        </div>
      <ul className="divide-y divide-gray-200">
        {payments.map((p) => (
          <li key={p.id}>
            <button
              onClick={() => onSelect(p.id)}
              className="w-full text-left px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-900">{p.customer_name}</p>
                  <p className="text-xs text-gray-500 mt-1">Order ID: {p.id} • {new Date(p.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {p.amount ? `Rs. ${p.amount.toLocaleString()}` : "Amount missing"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <StatusBadge decision={p.decision} />
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </button>
          </li>
        ))}
        {payments.length === 0 && (
          <li className="px-6 py-16 text-center">
            <ShieldCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-base font-semibold text-gray-800">No payment submissions yet</p>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1 mb-4">
              Your database is clean. Click below to upload and verify your first real bank transfer slip!
            </p>
            <button
              onClick={() => setShowUpload(true)}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Upload className="w-4 h-4 mr-2" /> Upload First Slip
            </button>
          </li>
        )}
      </ul>
      </div>
      
      {showUpload && (
        <UploadModal 
          onClose={() => setShowUpload(false)} 
          onSuccess={() => {
            setShowUpload(false);
            fetchPayments();
          }} 
        />
      )}
    </>
  );
}

function UploadModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [orderId, setOrderId] = useState('1');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an image file');
      return;
    }

    setUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('order_id', orderId);
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      onSuccess();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Upload Payment Slip</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500"><X className="w-5 h-5" /></button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="p-3 text-sm text-red-700 bg-red-50 rounded-md border border-red-200">{error}</div>}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Order Scenario</label>
            <select 
              value={orderId} 
              onChange={e => setOrderId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
            >
              <option value="1">Order #1 • John Doe (Expected: Rs. 25,000.00)</option>
              <option value="2">Order #2 • Jane Smith (Expected: Rs. 15,000.00)</option>
              <option value="3">Order #3 • Fraudster (Expected: Rs. 25,000.00)</option>
              <option value="4">Order #4 • John Doe (Expected: Rs. 25,000.00 - Duplicate)</option>
              <option value="5">Order #5 • John Doe (Expected: Rs. 25,000.00 - Reused)</option>
              <option value="6">Order #6 • Jane Smith (Expected: Rs. 5,000.00 - Blurry)</option>
              <option value="7">Order #7 • Jane Smith (Expected: Rs. 5,000.00 - Delayed SMS)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Select the order scenario corresponding to your test receipt.</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payment Image</label>
            <input 
              type="file" 
              accept="image/*"
              required
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 border border-gray-200 rounded-md"
            />
          </div>
          
          <div className="pt-4 flex justify-end gap-3 border-t border-gray-100 mt-6">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={uploading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading & Verifying...' : 'Upload & Verify'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DetailView({ id, onBack }: { id: number; onBack: () => void }) {
  const [detail, setDetail] = useState<PaymentDetail | null>(null);

  useEffect(() => {
    axios.get(`${API_BASE}/${id}`).then(res => setDetail(res.data)).catch(console.error);
  }, [id]);

  if (!detail) return <div className="text-center py-10">Loading details...</div>;

  let evidence = { flags: [] as string[] };
  try {
    evidence = JSON.parse(detail.verification.evidence_json);
  } catch (e) {}

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800">
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to dashboard
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">Payment Verification Report</h3>
            <p className="mt-1 text-sm text-gray-500">Order #{detail.order.id} for {detail.customer.name}</p>
          </div>
          <StatusBadge decision={detail.verification.decision} />
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Image & Customer details */}
          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Submitted Evidence</h4>
              <div className="bg-gray-100 rounded-lg h-64 flex items-center justify-center border border-gray-200 overflow-hidden">
                <img 
                  src={`http://localhost:8000${detail.image_path}`} 
                  alt="Payment Receipt" 
                  className="w-full h-full object-cover" 
                />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Customer Context</h4>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-4 text-sm">
                <div>
                  <dt className="text-gray-500">Customer</dt>
                  <dd className="font-medium text-gray-900">{detail.customer.name}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Phone</dt>
                  <dd className="font-medium text-gray-900">{detail.customer.phone}</dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Right Column: Verification Results */}
          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">System Conclusion</h4>
              <div className={cn(
                "rounded-lg p-4 border",
                detail.verification.decision === 'APPROVED' ? "bg-green-50 border-green-200" :
                detail.verification.decision === 'REJECTED' ? "bg-red-50 border-red-200" :
                "bg-yellow-50 border-yellow-200"
              )}>
                <p className="font-semibold text-gray-900 mb-1">{detail.verification.internal_reason}</p>
                <p className="text-sm text-gray-700">Confidence: {(detail.verification.confidence_score * 100).toFixed(0)}%</p>
                
                {evidence.flags && evidence.flags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {evidence.flags.map((f, i) => (
                      <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-white border border-gray-200 text-gray-600 shadow-sm">
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Expected (Order)</h4>
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-gray-500">Amount</dt>
                    <dd className="font-semibold text-gray-900">Rs. {detail.order.expected_amount.toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Account</dt>
                    <dd className="text-gray-900 font-mono">{detail.order.expected_account}</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Submitted / Extracted</h4>
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-gray-500">Amount</dt>
                    <dd className={cn(
                      "font-semibold", 
                      detail.submitted.amount !== detail.order.expected_amount ? "text-red-600" : "text-green-600"
                    )}>
                      {detail.submitted.amount ? `Rs. ${detail.submitted.amount.toLocaleString()}` : "Not found"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Account</dt>
                    <dd className="text-gray-900 font-mono">{detail.submitted.account_no || 'N/A'}</dd>
                  </div>
                </dl>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Bot Response Preview</h4>
              <div className="bg-blue-50 text-blue-900 text-sm p-4 rounded-lg border border-blue-100 italic">
                "{detail.verification.customer_message}"
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
