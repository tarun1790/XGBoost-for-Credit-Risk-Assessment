import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { customerAPI, predictionAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  Plus, 
  Search, 
  Trash2, 
  Edit, 
  Activity, 
  Loader, 
  AlertTriangle,
  X,
  UserCheck
} from 'lucide-react';

const CustomerDirectory = () => {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null); 
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);

  // Form fields
  const [form, setForm] = useState({
    sk_id_curr: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    amt_income_total: 100000,
    amt_credit: 300000,
    amt_annuity: 15000,
    age_years: 30,
    employment_years: 5,
    is_retired: false,
    own_car_age: '',
    region_rating_client: 2,
    ext_source_1: '',
    ext_source_2: '',
    ext_source_3: '',
    name_contract_type: 'Cash loans',
    code_gender: 'F',
    flag_own_car: 'N',
    flag_own_realty: 'Y',
    cnt_children: 0,
    name_income_type: 'Working',
    name_education_type: 'Secondary / secondary special',
    name_family_status: 'Married',
    name_housing_type: 'House / apartment',
  });

  const { isAnalyst, isAdmin } = useAuth();
  const navigate = useNavigate();

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const data = await customerAPI.list(search);
      setCustomers(data);
    } catch (err) {
      console.error(err);
      setError('Could not retrieve customers list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, [search]);

  const handleAssess = async (customerId) => {
    setActionLoading(customerId);
    try {
      const prediction = await predictionAPI.assess(customerId);
      navigate(`/predictions/${prediction.id}`);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Credit risk evaluation failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (customerId) => {
    if (!window.confirm('Confirm borrower deletion.')) {
      return;
    }
    try {
      await customerAPI.delete(customerId);
      loadCustomers();
    } catch (err) {
      console.error(err);
      alert('Action unauthorized.');
    }
  };

  const handleOpenCreateModal = () => {
    setEditingCustomer(null);
    setForm({
      sk_id_curr: Math.floor(100000 + Math.random() * 900000),
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      amt_income_total: 120000,
      amt_credit: 400000,
      amt_annuity: 20000,
      age_years: 35,
      employment_years: 6,
      is_retired: false,
      own_car_age: '',
      region_rating_client: 2,
      ext_source_1: 0.5,
      ext_source_2: 0.5,
      ext_source_3: 0.5,
      name_contract_type: 'Cash loans',
      code_gender: 'F',
      flag_own_car: 'N',
      flag_own_realty: 'Y',
      cnt_children: 0,
      name_income_type: 'Working',
      name_education_type: 'Secondary / secondary special',
      name_family_status: 'Married',
      name_housing_type: 'House / apartment',
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (customer) => {
    setEditingCustomer(customer);
    const ageY = Math.round(-customer.days_birth / 365.25);
    const isRet = customer.days_employed === 365243;
    const empY = isRet ? 0 : Math.round(-customer.days_employed / 365.25);

    setForm({
      sk_id_curr: customer.sk_id_curr,
      first_name: customer.first_name,
      last_name: customer.last_name,
      email: customer.email || '',
      phone: customer.phone || '',
      amt_income_total: customer.amt_income_total,
      amt_credit: customer.amt_credit,
      amt_annuity: customer.amt_annuity,
      age_years: ageY,
      employment_years: empY,
      is_retired: isRet,
      own_car_age: customer.own_car_age !== null ? customer.own_car_age : '',
      region_rating_client: customer.region_rating_client,
      ext_source_1: customer.ext_source_1 !== null ? customer.ext_source_1 : '',
      ext_source_2: customer.ext_source_2 !== null ? customer.ext_source_2 : '',
      ext_source_3: customer.ext_source_3 !== null ? customer.ext_source_3 : '',
      name_contract_type: customer.name_contract_type,
      code_gender: customer.code_gender,
      flag_own_car: customer.flag_own_car,
      flag_own_realty: customer.flag_own_realty,
      cnt_children: customer.cnt_children,
      name_income_type: customer.name_income_type,
      name_education_type: customer.name_education_type,
      name_family_status: customer.name_family_status,
      name_housing_type: customer.name_housing_type,
    });
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const daysBirth = -Math.round(form.age_years * 365.25);
    const daysEmployed = form.is_retired ? 365243 : -Math.round(form.employment_years * 365.25);
    const carAge = form.flag_own_car === 'Y' && form.own_car_age ? parseFloat(form.own_car_age) : null;
    const ext1 = form.ext_source_1 !== '' ? parseFloat(form.ext_source_1) : null;
    const ext2 = form.ext_source_2 !== '' ? parseFloat(form.ext_source_2) : null;
    const ext3 = form.ext_source_3 !== '' ? parseFloat(form.ext_source_3) : null;

    const payload = {
      ...form,
      days_birth: daysBirth,
      days_employed: daysEmployed,
      own_car_age: carAge,
      ext_source_1: ext1,
      ext_source_2: ext2,
      ext_source_3: ext3,
    };

    delete payload.age_years;
    delete payload.employment_years;
    delete payload.is_retired;

    try {
      if (editingCustomer) {
        await customerAPI.update(editingCustomer.id, payload);
      } else {
        await customerAPI.create(payload);
      }
      setIsModalOpen(false);
      loadCustomers();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to save customer details.');
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn font-mono">
      {/* Title block */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-neutral-900 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white uppercase tracking-wider">Borrowers Directory</h1>
          <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest">Register, edit, and evaluate credit scorecards</p>
        </div>
        {isAnalyst() && (
          <button onClick={handleOpenCreateModal} className="btn-primary flex items-center gap-2 self-start sm:self-auto text-xs">
            <Plus className="w-4 h-4" />
            Add Borrower Profile
          </button>
        )}
      </div>

      {/* Search block */}
      <div className="flex items-center gap-3 bg-black border border-neutral-850 rounded-none px-4 py-2.5 max-w-md">
        <Search className="w-4 h-4 text-neutral-500 shrink-0" />
        <input 
          type="text" 
          placeholder="SEARCH APPLICATION BY ID OR NAME..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent text-white border-none outline-none placeholder-neutral-600 text-xs focus:ring-0 uppercase"
        />
      </div>

      {error && (
        <div className="p-4 border border-white text-white bg-black text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Directory Table */}
      <div className="glass-panel rounded-none overflow-hidden border-neutral-800">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center">
            <Loader className="w-6 h-6 animate-spin text-white mb-2" />
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-widest">Querying profiles...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {customers.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-neutral-950 text-neutral-500 font-semibold border-b border-neutral-900 uppercase tracking-wider">
                    <th className="px-6 py-4">Borrower Name</th>
                    <th className="px-6 py-4">Application ID</th>
                    <th className="px-6 py-4">Annual Income</th>
                    <th className="px-6 py-4">Requested Credit</th>
                    <th className="px-6 py-4">Age / Employment</th>
                    <th className="px-6 py-4 text-right">Credit Evaluation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900">
                  {customers.map((customer) => {
                    const age = Math.round(-customer.days_birth / 365.25);
                    const employment = customer.days_employed === 365243 
                      ? 'PENSIONER' 
                      : `${Math.round(-customer.days_employed / 365.25)} YRS`;

                    return (
                      <tr key={customer.id} className="hover:bg-neutral-950 transition-colors uppercase">
                        <td className="px-6 py-4">
                          <div className="font-bold text-white">{customer.first_name} {customer.last_name}</div>
                          <div className="text-neutral-500 text-[10px] font-mono lowercase">{customer.email || 'no email'}</div>
                        </td>
                        <td className="px-6 py-4 font-mono text-neutral-300">{customer.sk_id_curr}</td>
                        <td className="px-6 py-4 text-neutral-300 font-mono">${customer.amt_income_total.toLocaleString()}</td>
                        <td className="px-6 py-4 text-neutral-300 font-mono">${customer.amt_credit.toLocaleString()}</td>
                        <td className="px-6 py-4 text-neutral-300">
                          <div>{age} yrs old</div>
                          <div className="text-neutral-500 text-[10px]">{employment}</div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {isAnalyst() && (
                              <>
                                <button
                                  onClick={() => handleAssess(customer.id)}
                                  className="px-3 py-1.5 bg-white text-black hover:bg-black hover:text-white border border-white text-[10px] font-bold uppercase flex items-center gap-1.5 transition-all duration-150 disabled:opacity-50"
                                  disabled={actionLoading !== null}
                                >
                                  {actionLoading === customer.id ? (
                                    <Loader className="w-3.5 h-3.5 animate-spin" />
                                  ) : (
                                    <Activity className="w-3.5 h-3.5" />
                                  )}
                                  Assess Risk
                                </button>
                                <button
                                  onClick={() => handleOpenEditModal(customer)}
                                  className="p-1.5 bg-black hover:bg-neutral-900 text-neutral-400 hover:text-white border border-neutral-800 hover:border-neutral-600 transition-colors"
                                  title="Edit Profile"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                              </>
                            )}
                            {isAdmin() && (
                              <button
                                onClick={() => handleDelete(customer.id)}
                                className="p-1.5 bg-black hover:bg-white text-neutral-400 hover:text-black border border-neutral-800 hover:border-white transition-colors"
                                title="Delete Profile"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="p-16 text-center text-neutral-600 uppercase tracking-widest text-xs">
                No borrower profiles registered.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal Dialog for Create/Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/95 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-black border border-white rounded-none w-full max-w-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-slideUp font-mono">
            {/* Modal Header */}
            <div className="p-6 border-b border-neutral-900 flex justify-between items-center bg-black">
              <h2 className="text-base font-black text-white flex items-center gap-2 uppercase tracking-wider">
                <UserCheck className="text-white w-5 h-5" />
                {editingCustomer ? 'Modify Profile' : 'Register Profile'}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-neutral-500 hover:text-white p-1">
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <form onSubmit={handleFormSubmit} className="p-6 overflow-y-auto space-y-6 flex-1">
              {error && (
                <div className="p-3 border border-white text-white bg-black text-xs flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Grid 1: Basic Identifiers */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Application ID (SK_ID)</label>
                  <input 
                    type="number" 
                    value={form.sk_id_curr}
                    onChange={(e) => setForm({...form, sk_id_curr: parseInt(e.target.value) || ''})}
                    className="form-input" 
                    required 
                    disabled={!!editingCustomer}
                  />
                </div>
                <div>
                  <label className="form-label">First Name</label>
                  <input 
                    type="text" 
                    value={form.first_name}
                    onChange={(e) => setForm({...form, first_name: e.target.value})}
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Last Name</label>
                  <input 
                    type="text" 
                    value={form.last_name}
                    onChange={(e) => setForm({...form, last_name: e.target.value})}
                    className="form-input" 
                    required 
                  />
                </div>
              </div>

              {/* Grid 2: Contacts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Email Address</label>
                  <input 
                    type="email" 
                    value={form.email}
                    onChange={(e) => setForm({...form, email: e.target.value})}
                    className="form-input" 
                  />
                </div>
                <div>
                  <label className="form-label">Phone Number</label>
                  <input 
                    type="text" 
                    value={form.phone}
                    onChange={(e) => setForm({...form, phone: e.target.value})}
                    className="form-input" 
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>

              <div className="border-t border-neutral-900 pt-4">
                <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4">Financial & Employment Details</h3>
              </div>

              {/* Grid 3: Income / Credit */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Annual Total Income ($)</label>
                  <input 
                    type="number" 
                    value={form.amt_income_total}
                    onChange={(e) => setForm({...form, amt_income_total: parseFloat(e.target.value) || 0})}
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Requested Credit ($)</label>
                  <input 
                    type="number" 
                    value={form.amt_credit}
                    onChange={(e) => setForm({...form, amt_credit: parseFloat(e.target.value) || 0})}
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Monthly Loan Annuity ($)</label>
                  <input 
                    type="number" 
                    value={form.amt_annuity}
                    onChange={(e) => setForm({...form, amt_annuity: parseFloat(e.target.value) || 0})}
                    className="form-input" 
                    required 
                  />
                </div>
              </div>

              {/* Grid 4: Contract Type & Income Type */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Contract Type</label>
                  <select 
                    value={form.name_contract_type} 
                    onChange={(e) => setForm({...form, name_contract_type: e.target.value})}
                    className="form-input"
                  >
                    <option value="Cash loans">Cash Loan</option>
                    <option value="Revolving loans">Revolving Credit</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Income Source Class</label>
                  <select 
                    value={form.name_income_type} 
                    onChange={(e) => setForm({...form, name_income_type: e.target.value})}
                    className="form-input"
                  >
                    <option value="Working">Working / Salaried</option>
                    <option value="Commercial associate">Commercial Associate</option>
                    <option value="State servant">State Servant / Govt</option>
                    <option value="Pensioner">Pensioner / Retired</option>
                    <option value="Unemployed">Unemployed</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Education Achieved</label>
                  <select 
                    value={form.name_education_type} 
                    onChange={(e) => setForm({...form, name_education_type: e.target.value})}
                    className="form-input"
                  >
                    <option value="Secondary / secondary special">Secondary Education</option>
                    <option value="Higher education">University Degree</option>
                    <option value="Incomplete higher">Undergraduate / Incomplete Higher</option>
                    <option value="Lower secondary">Lower Secondary</option>
                    <option value="Academic degree">Post-graduate (PhD/Master)</option>
                  </select>
                </div>
              </div>

              {/* Grid 5: Age, Employment, Retirement */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Age (in Years)</label>
                  <input 
                    type="number" 
                    value={form.age_years}
                    onChange={(e) => setForm({...form, age_years: parseInt(e.target.value) || 0})}
                    className="form-input" 
                    min={18} 
                    max={100}
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Years of Employment</label>
                  <input 
                    type="number" 
                    value={form.employment_years}
                    onChange={(e) => setForm({...form, employment_years: parseInt(e.target.value) || 0})}
                    className="form-input" 
                    disabled={form.is_retired}
                    required={!form.is_retired}
                  />
                </div>
                <div className="flex items-center pt-8">
                  <label className="flex items-center gap-2.5 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={form.is_retired}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setForm({
                          ...form, 
                          is_retired: checked, 
                          name_income_type: checked ? 'Pensioner' : 'Working',
                          employment_years: checked ? 0 : 5
                        });
                      }}
                      className="w-4 h-4 rounded-none border-neutral-800 bg-black text-white focus:ring-0 focus:ring-offset-0"
                    />
                    <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">Pensioner / Unemployed</span>
                  </label>
                </div>
              </div>

              <div className="border-t border-neutral-900 pt-4">
                <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4">External Bureau Ratings (Scale 0.0 to 1.0)</h3>
              </div>

              {/* Grid 6: Bureau Sources */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">External Source 1</label>
                  <input 
                    type="number" 
                    step="0.001"
                    min="0"
                    max="1"
                    value={form.ext_source_1}
                    onChange={(e) => setForm({...form, ext_source_1: e.target.value})}
                    className="form-input" 
                    placeholder="0.500"
                  />
                </div>
                <div>
                  <label className="form-label">External Source 2</label>
                  <input 
                    type="number" 
                    step="0.001"
                    min="0"
                    max="1"
                    value={form.ext_source_2}
                    onChange={(e) => setForm({...form, ext_source_2: e.target.value})}
                    className="form-input" 
                    placeholder="0.500"
                  />
                </div>
                <div>
                  <label className="form-label">External Source 3</label>
                  <input 
                    type="number" 
                    step="0.001"
                    min="0"
                    max="1"
                    value={form.ext_source_3}
                    onChange={(e) => setForm({...form, ext_source_3: e.target.value})}
                    className="form-input" 
                    placeholder="0.500"
                  />
                </div>
              </div>

              <div className="border-t border-neutral-900 pt-4">
                <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4">Asset Details & Social Demographics</h3>
              </div>

              {/* Grid 7: Assets & Family */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Gender</label>
                  <select 
                    value={form.code_gender} 
                    onChange={(e) => setForm({...form, code_gender: e.target.value})}
                    className="form-input"
                  >
                    <option value="F">Female</option>
                    <option value="M">Male</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Car Owner</label>
                  <select 
                    value={form.flag_own_car} 
                    onChange={(e) => setForm({...form, flag_own_car: e.target.value, own_car_age: e.target.value === 'N' ? '' : form.own_car_age})}
                    className="form-input"
                  >
                    <option value="N">No</option>
                    <option value="Y">Yes</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Car Age (in Years)</label>
                  <input 
                    type="number" 
                    value={form.own_car_age}
                    onChange={(e) => setForm({...form, own_car_age: e.target.value})}
                    className="form-input" 
                    disabled={form.flag_own_car === 'N'}
                    placeholder="None"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">House Owner</label>
                  <select 
                    value={form.flag_own_realty} 
                    onChange={(e) => setForm({...form, flag_own_realty: e.target.value})}
                    className="form-input"
                  >
                    <option value="Y">Yes</option>
                    <option value="N">No</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Children Count</label>
                  <input 
                    type="number" 
                    value={form.cnt_children}
                    onChange={(e) => setForm({...form, cnt_children: parseInt(e.target.value) || 0})}
                    className="form-input" 
                    min={0}
                  />
                </div>
                <div>
                  <label className="form-label">Housing Situation</label>
                  <select 
                    value={form.name_housing_type} 
                    onChange={(e) => setForm({...form, name_housing_type: e.target.value})}
                    className="form-input"
                  >
                    <option value="House / apartment">Owns House / Apartment</option>
                    <option value="Rented apartment">Rented Apartment</option>
                    <option value="With parents">Living With Parents</option>
                    <option value="Municipal apartment">Municipal Apartment</option>
                    <option value="Office apartment">Office Apartment</option>
                  </select>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="border-t border-neutral-900 pt-6 flex justify-end gap-3 bg-black -mx-6 -mb-6 p-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingCustomer ? 'Update Profile' : 'Register Borrower'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerDirectory;
