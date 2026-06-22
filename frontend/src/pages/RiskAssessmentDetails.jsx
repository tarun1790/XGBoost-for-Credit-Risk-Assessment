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
        setError('Could not fetch assessment report.');
      } finally {
        setLoading(false);
      }
    };
    fetchPrediction();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)]">
        <Loader className="w-6 h-6 animate-spin text-white mb-2" />
        <span className="text-neutral-500 font-bold uppercase text-[10px] tracking-widest font-mono">Compiling Audit...</span>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="space-y-4 p-8 border border-white bg-black rounded-none text-center max-w-md mx-auto mt-12 font-mono">
        <ShieldAlert className="w-10 h-10 text-white mx-auto" />
        <h3 className="text-sm font-bold uppercase tracking-wider text-white">Report Unobtainable</h3>
        <p className="text-neutral-500 text-xs">{error || 'Prediction record does not exist.'}</p>
        <button onClick={() => navigate('/')} className="btn-secondary py-2 mt-4 inline-flex items-center gap-2 text-xs">
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
  const shapChartData = Object.entries(shap_explanations)
    .map(([name, val]) => ({
      rawName: name,
      name: formatFeatureName(name),
      value: parseFloat(val)
    }))
    .filter(item => Math.abs(item.value) > 0.005) 
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value)) 
    .slice(0, 10) 
    .reverse(); 

  // Calibrate score Progress Gauge (300-850 scale)
  const radius = 85;
  const strokeWidth = 12;
  const circumference = 2 * Math.PI * radius;
  const scoreOffset = Math.max(300, Math.min(850, credit_score));
  const progressPercent = (scoreOffset - 300) / 550;
  const strokeDashoffset = circumference - (progressPercent * circumference);

  return (
    <div className="space-y-6 animate-fadeIn font-mono">
      {/* Back button header */}
      <div className="flex items-center gap-4 border-b border-neutral-900 pb-5">
        <Link to="/" className="p-2 bg-black hover:bg-white text-white hover:text-black border border-neutral-850 hover:border-white transition-all duration-150">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Evaluation Audit Report</span>
          <h1 className="text-xl font-black text-white uppercase">Borrower: {customer.first_name} {customer.last_name}</h1>
        </div>
      </div>

      {/* Main Grid: Score Gauge and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Credit Score gauge Card */}
        <div className="glass-panel p-6 rounded-none flex flex-col items-center justify-center text-center space-y-5 border-neutral-800 relative overflow-hidden">
          {/* Futuristic Corner Brackets */}
          <div className="absolute top-2 left-2 w-3.5 h-3.5 border-t-2 border-l-2 border-neutral-800" />
          <div className="absolute top-2 right-2 w-3.5 h-3.5 border-t-2 border-r-2 border-neutral-800" />
          <div className="absolute bottom-2 left-2 w-3.5 h-3.5 border-b-2 border-l-2 border-neutral-800" />
          <div className="absolute bottom-2 right-2 w-3.5 h-3.5 border-b-2 border-r-2 border-neutral-800" />

          <h3 className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Credit Rating Scorecard</h3>
          
          {/* Animated SVG Circle Progress Gauge with Tech HUD Overlay */}
          <div className="relative flex items-center justify-center w-52 h-52">
            <svg className="w-full h-full -rotate-90">
              {/* Outer tick ring */}
              <circle cx="104" cy="104" r={radius + 12} stroke="#1f1f1f" strokeWidth="1.5" strokeDasharray="3 5" fill="transparent" />
              {/* Inner tick ring */}
              <circle cx="104" cy="104" r={radius - 12} stroke="#111111" strokeWidth="3" strokeDasharray="1 8" fill="transparent" />
              
              {/* Grid crosshair guides */}
              <line x1="104" y1="5" x2="104" y2="15" stroke="#262626" strokeWidth="1" />
              <line x1="104" y1="193" x2="104" y2="203" stroke="#262626" strokeWidth="1" />
              <line x1="5" y1="104" x2="15" y2="104" stroke="#262626" strokeWidth="1" />
              <line x1="193" y1="104" x2="203" y2="104" stroke="#262626" strokeWidth="1" />

              {/* Main gauge track */}
              <circle
                cx="104"
                cy="104"
                r={radius}
                className="stroke-neutral-900"
                strokeWidth={strokeWidth}
                fill="transparent"
              />
              {/* Main progress gauge */}
              <circle
                cx="104"
                cy="104"
                r={radius}
                stroke="#ffffff"
                strokeWidth={strokeWidth}
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="square"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-white tracking-tight">{credit_score}</span>
              <span className="text-neutral-500 text-[9px] uppercase font-bold tracking-widest mt-0.5">Rating</span>
              <span className="text-neutral-600 text-[8px] mt-1">Scale: 300 - 850</span>
            </div>
          </div>

          <div className="w-full p-4 border border-neutral-850 bg-neutral-950 text-center space-y-1">
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Risk Category</span>
            <div className="text-sm font-bold uppercase tracking-wider text-white">
              {risk_category}
            </div>
          </div>

          <div className="w-full grid grid-cols-2 gap-3 text-xs">
            <div className="bg-black border border-neutral-850 p-3 rounded-none flex flex-col items-start">
              <span className="text-neutral-500 text-[9px] font-bold uppercase tracking-wider">Default Prob (PD)</span>
              <span className="text-base font-bold text-white mt-1">{pdPercent}%</span>
            </div>
            <div className="bg-black border border-neutral-850 p-3 rounded-none flex flex-col items-start">
              <span className="text-neutral-500 text-[9px] font-bold uppercase tracking-wider">Approval</span>
              <span className="text-base font-bold text-white mt-1">
                {credit_score >= 600 ? 'APPROVED' : 'DECLINED'}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Customer Details Cards */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-none flex flex-col justify-between border-neutral-800">
          <div className="border-b border-neutral-900 pb-4 mb-5 flex items-center justify-between">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Borrower Profile Data</h4>
            <div className="flex items-center gap-1.5 text-neutral-500 text-[10px] uppercase font-bold">
              <Calendar className="w-3.5 h-3.5" />
              Date: {new Date(prediction.assessed_at).toLocaleDateString()}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3.5 text-xs flex-1 uppercase">
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><User className="w-3.5 h-3.5" /> Full Name</span>
              <span className="font-bold text-neutral-200">{customer.first_name} {customer.last_name}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><Scale className="w-3.5 h-3.5" /> App ID</span>
              <span className="font-bold text-neutral-200">{customer.sk_id_curr}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5" /> Total Income</span>
              <span className="font-bold text-neutral-200">${customer.amt_income_total.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5" /> Credit Size</span>
              <span className="font-bold text-neutral-200">${customer.amt_credit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5" /> Annuity Size</span>
              <span className="font-bold text-neutral-200">${customer.amt_annuity.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> Age</span>
              <span className="font-bold text-neutral-200">{age} yrs</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><Briefcase className="w-3.5 h-3.5" /> Employed</span>
              <span className="font-bold text-neutral-200">{emp}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5"><HelpCircle className="w-3.5 h-3.5" /> Education</span>
              <span className="font-bold text-neutral-200 truncate max-w-[150px]">{customer.name_education_type.replace('secondary special', 'special')}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5">💼 Income Class</span>
              <span className="font-bold text-neutral-200">{customer.name_income_type}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-neutral-900">
              <span className="text-neutral-500 flex items-center gap-1.5">🏠 Housing</span>
              <span className="font-bold text-neutral-200">{customer.name_housing_type.replace('House / apartment', 'Own House')}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-neutral-900 flex items-center gap-4 text-[10px] text-neutral-500">
            <div>
              <span className="font-bold text-neutral-400">Bureau A:</span> {customer.ext_source_1 !== null ? customer.ext_source_1.toFixed(3) : 'Missing'}
            </div>
            <div>
              <span className="font-bold text-neutral-400">Bureau B:</span> {customer.ext_source_2 !== null ? customer.ext_source_2.toFixed(3) : 'Missing'}
            </div>
            <div>
              <span className="font-bold text-neutral-400">Bureau C:</span> {customer.ext_source_3 !== null ? customer.ext_source_3.toFixed(3) : 'Missing'}
            </div>
          </div>
        </div>
      </div>

      {/* SHAP Explanation Section */}
      <div className="glass-panel p-6 rounded-none border-neutral-800 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-900 pb-4">
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="text-white w-4.5 h-4.5" />
              Explainable AI: Model Feature Contribution (SHAP)
            </h3>
            <p className="text-neutral-500 text-[10px] uppercase tracking-wider mt-1">
              Diverging attributions shifting Probability of Default (PD) relative to baseline log-odds.
            </p>
          </div>
          <div className="flex items-center gap-3 text-[10px] font-bold uppercase">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 bg-white shrink-0 border border-neutral-700" /> Pushes Risk Up (Bad)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 bg-neutral-600 shrink-0 border border-neutral-700" /> Pushes Risk Down (Good)</span>
          </div>
        </div>

        {/* Recharts Diverging Bar Chart */}
        <div className="h-96 text-xs">
          {shapChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={shapChartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222222" />
                <XAxis type="number" stroke="#666666" fontSize={10} />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  stroke="#888888" 
                  fontSize={10} 
                  width={200}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const isRiskUp = data.value > 0;
                      return (
                        <div className="bg-black p-3 border border-white rounded-none text-[10px] space-y-1 font-mono uppercase text-white">
                          <p className="font-bold text-white">{data.name}</p>
                          <p className="text-neutral-500">SHAP: {data.value.toFixed(4)}</p>
                          <p className="font-semibold">
                            {isRiskUp 
                              ? 'Increases probability of default' 
                              : 'Decreases probability of default'}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <ReferenceLine x={0} stroke="#666666" strokeWidth={1} />
                <Bar dataKey="value">
                  {shapChartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.value > 0 ? '#ffffff' : '#666666'} 
                      stroke="#000000"
                      strokeWidth={1}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center border border-dashed border-neutral-900">
              <span className="text-neutral-600 text-xs font-mono uppercase tracking-widest">No explanations data</span>
            </div>
          )}
        </div>

        <div className="bg-neutral-950 border border-neutral-900 p-4 text-[10px] text-neutral-500 leading-normal uppercase">
          <span className="font-bold text-neutral-300 block mb-1">Interpretation:</span>
          Each bar represents a feature's mathematical contribution to the XGBoost booster.
          <ul className="list-disc pl-5 mt-1.5 space-y-1 text-neutral-600">
            <li>
              <strong className="text-white">Positive SHAP values (white bars)</strong> represent adverse risk factors that pushed default probability higher, resulting in a lower credit score.
            </li>
            <li>
              <strong className="text-neutral-400">Negative SHAP values (gray bars)</strong> represent favorable risk mitigators that lowered default probability, lifting the final score.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RiskAssessmentDetails;
