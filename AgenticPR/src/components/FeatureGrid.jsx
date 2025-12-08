export const FeatureGrid = ({ features }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {features.map((feature, index) => (
        <div key={index} className="box-border caret-transparent outline-transparent">
          <div className="flex items-center gap-4 mb-4">
            <img
              src={feature.iconUrl}
              alt={feature.title}
              className={`box-border caret-transparent shrink-0 h-6 outline-transparent w-6 ${feature.iconClassName || ''}`}
            />
            <h4 className="text-[17px] font-[510] box-border caret-transparent leading-6 outline-transparent">
              {feature.title}
            </h4>
          </div>
          <p className="text-neutral-400 text-[15px] box-border caret-transparent leading-[22px] outline-transparent">
            {feature.description}
          </p>
        </div>
      ))}
    </div>
  );
};
