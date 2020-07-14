%{
    The following code takes in the mall_gt.mat file from the mall dataset
    and converts it into a CSV file format
%}
load('mall_gt.mat');
csv_path = 'mall_GT.csv';
dlmwrite(csv_path, strcat('id,filename,count,locations'), 'delimiter', '');

i = 0 ;
for b = frame 
    i = i + 1;  
    a = b(1);
    XY = a{1,1}.loc; 
    a = [XY(:,2), XY(:,1)];
    a = mat2str(a); 
    a = strrep(a,';','] [');
    a = strrep(a,' ',', '); 
    fname = strcat('seq_', num2str(i,'%06.f'), '.jpg');
    p =  strcat(num2str(i),',',fname,',',num2str(count(i)), ',"[', a,']"');
    display(p); 
    dlmwrite(csv_path,p,'delimiter','','-append');
end
 