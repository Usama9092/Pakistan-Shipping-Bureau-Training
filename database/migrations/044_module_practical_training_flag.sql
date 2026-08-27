alter table qualification_modules add column practical_training_required text default 'No';

update qualification_modules
set practical_training_required = case when module_type = 'Practical Training' then 'Yes' else 'No' end
where practical_training_required is null or practical_training_required = '';
