import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { predictionAPI } from '../services/api';
import { 
  ArrowLeft, 
  ShieldAlert, 
  ShieldCheck, 
  Calendar, 
  User, 
  TrendingUp, 
  Briefcase, 
  Scale, 
  DollarSign, 
  Loader,
  HelpCircle
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ReferenceLine, 
  ResponsiveContainer 
} from 'recharts';

// Feature name mapper for borrower-friendly visualization
const formatFeatureName = (name) => {
  const mapping = {
    'EXT_SOURCE_2': 'Credit Bureau Score (Source B)',
    'EXT_SOURCE_3': 'Credit Bureau Score (Source C)',
    'EXT_SOURCE_1': 'Credit Bureau Score (Source A)',
    'EXT_SOURCES_MEAN': 'Average Bureau Rating',
    'CREDIT_INCOME_PERCENT': 'Loan-to-Income Ratio',
    'ANNUITY_INCOME_PERCENT': 'Annuity-to-Income Ratio',
    'CREDIT_TERM': 'Loan Payment Term Rate',
    'DAYS_EMPLOYED_PERCENT': 'Employment-to-Age Ratio',
    'AGE_YEARS': 'Applicant Age',
    'AMT_INCOME_TOTAL': 'Total Annual Income',
    'AMT_CREDIT': 'Requested Loan Principal',
    'AMT_ANNUITY': 'Requested Monthly Annuity',
    'AMT_GOODS_PRICE': 'Goods Purchase Price',
    'REGION_RATING_CLIENT': 'Client Region Rating',
    'CNT_CHILDREN': 'Children Dependent Count',
    'CNT_FAM_MEMBERS': 'Family Members Count',
    'OWN_CAR_AGE': 'Vehicle Age',
    'DAYS_EMPLOYED_ANOM': 'Unemployed / Pensioner Flag',
    'DAYS_EMPLOYED_CLEANED': 'Days Employed',
    'EXT_SOURCES_NAN_COUNT': 'Missing Bureau Ratings Count',
    'EXT_SOURCES_GEOM_MEAN': 'Geometric Mean Bureau Rating',
    
    // One hot encoded categories
    'NAME_EDUCATION_TYPE_Higher education': 'Education: University Degree',
    'NAME_EDUCATION_TYPE_Secondary / secondary special': 'Education: Secondary/High School',
    'NAME_INCOME_TYPE_Working': 'Income: Standard Employee',
    'NAME_INCOME_TYPE_Pensioner': 'Income: Pensioner/Retired',
    'NAME_INCOME_TYPE_Commercial associate': 'Income: Business Owner/Associate',
    'NAME_INCOME_TYPE_State servant': 'Income: Public Servant',
    'NAME_FAMILY_STATUS_Married': 'Family Status: Married',
    'NAME_FAMILY_STATUS_Single / not married': 'Family Status: Single',
    'NAME_HOUSING_TYPE_House / apartment': 'Housing: Owns House/Apartment',
    'NAME_HOUSING_TYPE_Rented apartment': 'Housing: Rented Apartment',
    'CODE_GENDER_M': 'Gender: Male',
    'CODE_GENDER_F': 'Gender: Female',
    'FLAG_OWN_CAR_Y': 'Owns Vehicle',
    'FLAG_OWN_CAR_N': 'Does Not Own Vehicle',
    'FLAG_OWN_REALTY_Y': 'Owns Real Estate',
    'FLAG_OWN_REALTY_N': 'Does Not Own Real Estate',
    'NAME_CONTRACT_TYPE_Cash loans': 'Contract Type: Cash Loan',
    'NAME_CONTRACT_TYPE_Revolving loans': 'Contract Type: Revolving Line'
  };

  if (mapping[name]) return mapping[name];
  
  // Generic formatter fallback for unnamed encoded categories
  return name
    .replace('NAME_INCOME_TYPE_', 'Income Class: ')
    .replace('NAME_EDUCATION_TYPE_', 'Education: ')
    .replace('NAME_FAMILY_STATUS_', 'Family: ')
    .replace('NAME_HOUSING_TYPE_', 'Housing: ')
    .replace(/_/g, ' ');
};

const RiskAssessmentDetails = () => {
  const { id } = useParams();
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPrediction = async () => {
      setLoading(true);
      try {
        const data = await predictionAPI.getDetails(id);
        setPrediction(data);
      } catch (err) {
        console.error(err);
        setError('Could not retrieve risk assessment report details.');
      } finally {
        setLoading(false);
      }
    };
    fetchPrediction();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-100px)]">
        <Loader className="w-8 h-8 animate-spin text-brand-accent mb-3" />
        <span className="text-slate-400 font-medium ml-3">Compiling credit evaluation audit...</span>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="space-y-4 p-8 glass-panel rounded-xl text-center max-w-md mx-auto mt-12">
        <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-lg font-bold text-white">Report Unobtainable</h3>
        <p className="text-slate-400 text-sm">{error || 'Prediction record does not exist.'}</p>
        <button onClick={() => navigate('/')} className="btn-secondary py-2 mt-4 inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>
      </div>
    );
  }

  const { customer, credit_score, probability_of_default, risk_category, shap_explanations } = prediction;
  const pdPercent = (probability_of_default * 100).toFixed(2);
  const age = Math.round(-customer.days_birth / 365.25);
  const emp = customer.days_employed === 365243 ? 'Retired / Pensioner' : `${Math.round(-customer.days_employed / 365.25)} years`;

  // Process SHAP values for the chart
  // Filter out features with near zero contribution and sort by absolute magnitude
  const shapChartData = Object.entries(shap_explanations)
    .map(([name, val]) => ({
      rawName: name,
      name: formatFeatureName(name),
      value: parseFloat(val)
    }))
    .filter(item => Math.abs(item.value) > 0.005) // Filter out noise
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value)) // Sort by absolute strength
    .slice(0, 10) // Select top 10 influencers
    .reverse(); // Reverse for horizontal layout order (top at the top)

  // Calibrate score Progress Gauge (300-850 scale)
  const radius = 85;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const scoreOffset = Math.max(300, Math.min(850, credit_score));
  const progressPercent = (scoreOffset - 300) / 550;
  const strokeDashoffset = circumference - (progressPercent * circumference);

  // Set colors according to risk tiers
  let ratingColorClass = "text-rose-500";
  let ratingBorderClass = "border-rose-500/20 bg-rose-500/5";
  let gaugeColor = "#f43f5e"; // rose

  if (credit_score >= 750) {
    ratingColorClass = "text-emerald-400";
    ratingBorderClass = "border-emerald-500/20 bg-emerald-500/5";
    gaugeColor = "#10b981"; // emerald
  } else if (credit_score >= 700) {
    ratingColorClass = "text-blue-400";
    ratingBorderClass = "border-blue-500/20 bg-blue-500/5";
    gaugeColor = "#60a5fa"; // blue
  } else if (credit_score >= 600) {
    ratingColorClass = "text-amber-400";
    ratingBorderClass = "border-amber-500/20 bg-amber-500/5";
    gaugeColor = "#f59e0b"; // amber
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Back button header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="p-2 bg-brand-card hover:bg-slate-700/60 text-slate-400 hover:text-white rounded-lg border border-slate-700/80 transition-all duration-150">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Evaluation Audit Report</span>
          <h1 className="text-2xl font-bold text-white">Risk Profile: {customer.first_name} {customer.last_name}</h1>
        </div>
      </div>

      {/* Main Grid: Score Gauge and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Credit Score gauge Card */}
        <div className="glass-panel p-6 rounded-xl flex flex-col items-center justify-center text-center space-y-5">
          <h3 className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Computed Credit Rating</h3>
          
          {/* Animated SVG Circle Progress Gauge */}
          <div className="relative flex items-center justify-center w-52 h-52">
            <svg className="w-full h-full -rotate-90">
              {/* Background ring */}
              <circle
                cx="104"
                cy="104"
                r={radius}
                className="stroke-slate-800"
                strokeWidth={strokeWidth}
                fill="transparent"
              />
              {/* Score filling ring */}
              <circle
                cx="104"
                cy="104"
                r={radius}
                stroke={gaugeColor}
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            {/* Center score readout */}
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-4xl font-extrabold text-white tracking-tight">{credit_score}</span>
              <span className="text-slate-400 text-[10px] uppercase font-semibold tracking-wider mt-0.5">Score Card</span>
              <span className="text-slate-500 text-[9px] mt-1 font-mono">Scale: 300 - 850</span>
            </div>
          </div>

          <div className={`w-full p-4.5 rounded-xl border ${ratingBorderClass} text-center space-y-1`}>
            <span className="text-slate-400 text-xs font-medium">Risk Status Classification</span>
            <div className={`text-base font-bold uppercase tracking-wide ${ratingColorClass}`}>
              {risk_category}
            </div>
          </div>

          <div className="w-full grid grid-cols-2 gap-3 text-sm">
            <div className="bg-brand-card/40 border border-slate-800/80 p-3 rounded-lg flex flex-col">
              <span className="text-slate-500 text-[10px] font-semibold uppercase">Default Prob (PD)</span>
              <span className="text-lg font-bold text-slate-100 mt-1">{pdPercent}%</span>
            </div>
            <div className="bg-brand-card/40 border border-slate-800/80 p-3 rounded-lg flex flex-col">
              <span className="text-slate-500 text-[10px] font-semibold uppercase">Approval Status</span>
              <span className={`text-lg font-bold mt-1 ${credit_score >= 600 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {credit_score >= 600 ? 'Approved' : 'Declined'}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Customer Details Cards */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-xl flex flex-col justify-between">
          <div className="border-b border-slate-850 pb-4 mb-5 flex items-center justify-between">
            <h4 className="text-lg font-bold text-slate-100">Borrower Information Profile</h4>
            <div className="flex items-center gap-1 text-slate-500 text-xs">
              <Calendar className="w-4 h-4" />
              Assessed: {new Date(prediction.assessed_at).toLocaleDateString()}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm flex-1">
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><User className="w-4 h-4" /> Full Name</span>
              <span className="font-semibold text-slate-200">{customer.first_name} {customer.last_name}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><Scale className="w-4 h-4" /> Application ID</span>
              <span className="font-mono text-slate-200">{customer.sk_id_curr}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><DollarSign className="w-4 h-4" /> Annual Income</span>
              <span className="font-semibold text-slate-200">${customer.amt_income_total.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><TrendingUp className="w-4 h-4" /> Loan Credit Size</span>
              <span className="font-semibold text-slate-200">${customer.amt_credit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><DollarSign className="w-4 h-4" /> Monthly Annuity</span>
              <span className="font-semibold text-slate-200">${customer.amt_annuity.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><Calendar className="w-4 h-4" /> Age</span>
              <span className="font-semibold text-slate-200">{age} years</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><Briefcase className="w-4 h-4" /> Employment Term</span>
              <span className="font-semibold text-slate-200">{emp}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5"><HelpCircle className="w-4 h-4" /> Education Level</span>
              <span className="font-semibold text-slate-200">{customer.name_education_type.replace('secondary special', 'special')}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5">🔑 Income Source</span>
              <span className="font-semibold text-slate-200">{customer.name_income_type}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800/40">
              <span className="text-slate-500 flex items-center gap-1.5">🏠 Housing Condition</span>
              <span className="font-semibold text-slate-200">{customer.name_housing_type.replace('House / apartment', 'Own House')}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-850 flex items-center gap-4 text-xs text-slate-500">
            <div>
              <span className="font-semibold text-slate-400">External Bureau A:</span> {customer.ext_source_1 !== null ? customer.ext_source_1.toFixed(3) : 'Missing'}
            </div>
            <div>
              <span className="font-semibold text-slate-400">Bureau B:</span> {customer.ext_source_2 !== null ? customer.ext_source_2.toFixed(3) : 'Missing'}
            </div>
            <div>
              <span className="font-semibold text-slate-400">Bureau C:</span> {customer.ext_source_3 !== null ? customer.ext_source_3.toFixed(3) : 'Missing'}
            </div>
          </div>
        </div>
      </div>

      {/* SHAP Explanation Section */}
      <div className="glass-panel p-6 rounded-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-850 pb-4">
          <div>
            <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="text-brand-accent w-6 h-6" />
              Explainable AI: Model Feature Contribution (SHAP)
            </h3>
            <p className="text-slate-400 text-xs mt-1">
              Diverging impact of features shifting the Probability of Default (PD) relative to the baseline value.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-rose-500 shrink-0" /> Pushes Risk Up (Bad)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-500 shrink-0" /> Pushes Risk Down (Good)</span>
          </div>
        </div>

        {/* Recharts Diverging Bar Chart */}
        <div className="h-96">
          {shapChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={shapChartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  stroke="#94a3b8" 
                  fontSize={10.5} 
                  width={200}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const isRiskUp = data.value > 0;
                      return (
                        <div className="bg-brand-panel p-3 border border-slate-700 rounded-lg shadow-xl text-xs space-y-1">
                          <p className="font-bold text-slate-100">{data.name}</p>
                          <p className="text-slate-400 font-mono">SHAP: {data.value.toFixed(4)}</p>
                          <p className={`font-semibold ${isRiskUp ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {isRiskUp 
                              ? '⚠️ Increases borrower probability of default' 
                              : '✅ Decreases borrower probability of default'}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <ReferenceLine x={0} stroke="#475569" strokeWidth={1.5} />
                <Bar dataKey="value">
                  {shapChartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.value > 0 ? '#f43f5e' : '#10b981'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center border border-dashed border-slate-800 rounded-lg">
              <span className="text-slate-500 text-sm">Feature explanation generation failed. Verify SHAP library.</span>
            </div>
          )}
        </div>

        <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-xl text-xs text-slate-400 leading-relaxed">
          <span className="font-semibold text-slate-200 block mb-1">How to interpret this analysis:</span>
          Each bar represents a feature's mathematical contribution to the XGBoost credit scoring booster.
          <ul className="list-disc pl-5 mt-1.5 space-y-1">
            <li>
              <strong className="text-rose-400">Positive SHAP values (red bars)</strong> represent adverse risk factors (e.g., high debt ratios, low bureau scores) that pushed the probability of default higher, resulting in a lower credit score.
            </li>
            <li>
              <strong className="text-emerald-400">Negative SHAP values (green bars)</strong> represent favorable risk mitigators (e.g., higher bureau ratings, stable employment length) that lowered default probability, lifting the final scaled credit score.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RiskAssessmentDetails;
