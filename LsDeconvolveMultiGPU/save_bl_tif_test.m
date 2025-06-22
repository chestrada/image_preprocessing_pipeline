function save_bl_tif_test
% Extended regression + benchmark for save_bl_tif MEX

fprintf("🧪  save_bl_tif extended test-suite\n");

%% ---------- sandbox (deleted on exit) ----------
tmpRoot = tempname;   mkdir(tmpRoot);
cSandbox = onCleanup(@() sandbox_cleanup(tmpRoot));

%% ---------- A. basic 2-D / 3-D-singleton ----------
rng(42);
vol2d = uint8(randi(255,[256 256]));
fn2d  = fullfile(tmpRoot,'basic_2d.tif');
save_bl_tif(vol2d,{fn2d},false,'none');
assert(isequal(imread(fn2d),vol2d));

vol3d = reshape(vol2d,256,256,1);
fn3d  = fullfile(tmpRoot,'basic_3d.tif');
save_bl_tif(vol3d,{fn3d},false,'none');
assert(isequal(imread(fn3d),vol3d(:,:,1)));

fprintf("   ✅ basic 2-D / 3-D paths ok\n");

%% ---------- B. full matrix: {layout × dtype × compression} + per-test timing ----------
cfg.order = {'YXZ',false; 'XYZ',true};
cfg.dtype = {'uint8',@uint8; 'uint16',@uint16};
cfg.comp  = {'none','lzw','deflate'};
sz        = [2048 1024 4];  % ≥ 2 MiB slice

nLayouts = size(cfg.order,1);
nTypes   = size(cfg.dtype,1);
nComps   = numel(cfg.comp);
times    = zeros(nLayouts,nTypes,nComps);
speeds   = zeros(nLayouts,nTypes,nComps);

for o = 1:nLayouts
    fprintf("\n   🏁 Testing layout: %s\n", cfg.order{o,1});
    for d = 1:nTypes
        bytesPerSample = strcmp(cfg.dtype{d,1},'uint16') * 1 + 1;  % uint8→1, uint16→2
        for c = 1:nComps
            % prepare volume & permute if needed
            V = cfg.dtype{d,2}(randi(intmax(cfg.dtype{d,1}), sz));
            if cfg.order{o,2}
                V = permute(V,[2 1 3]);
            end

            % build file list
            tagSafe = regexprep(sprintf('%s_%s_%s',cfg.order{o,1},...
                          cfg.dtype{d,1},cfg.comp{c}), '[^A-Za-z0-9]','_');
            files = arrayfun(@(k) fullfile(tmpRoot, ...
                     sprintf('t_%s_%02d.tif',tagSafe,k)), 1:sz(3), 'Uni',false);

            % time the write+verify
            t0 = tic;
            save_bl_tif(V, files, cfg.order{o,2}, cfg.comp{c});
            tElapsed = toc(t0);

            % sanity-check
            for k = 1:sz(3)
                ref = V(:,:,k);
                if cfg.order{o,2}, ref = ref.'; end
                assert(isequal(imread(files{k}), ref), ...
                    "Mismatch %s slice %d", tagSafe, k);
            end

            % record
            times(o,d,c)  = tElapsed;
            MiB = prod(sz(1:2)) * bytesPerSample * sz(3) / 2^20;
            speeds(o,d,c)= MiB / tElapsed;

            fprintf("      ✅ %-30s in %.2f s (%.1f MiB/s)\n", ...
                    strrep(sprintf('%s_%s_%s',cfg.order{o,1},...
                    cfg.dtype{d,1},cfg.comp{c}),'_',' | '), ...
                    tElapsed, speeds(o,d,c));
        end
    end
end

%% ---------- C. guard-clause checks ----------
fprintf("\n   🛡  guard-clause checks\n");
try
    save_bl_tif(uint8(0), {'/no/way/out.tif'}, false,'lzw');
    error("invalid-path accepted");
catch, fprintf("      ✅ invalid path rejected\n"); end

roFile = fullfile(tmpRoot,'readonly.tif');
imwrite(uint8(1),roFile);  fileattrib(roFile,'-w');
cRO = onCleanup(@() restore_rw(roFile));

try
    save_bl_tif(uint8(0), {roFile}, false,'none');
    error("read-only overwrite accepted");
catch, fprintf("      ✅ read-only overwrite rejected\n"); end

%% ---------- D. layout performance table ----------
fprintf("\n   📊 Detailed performance comparison:\n");
totalEntries = nLayouts * nTypes * nComps;
Layout   = strings(totalEntries,1);
DType    = strings(totalEntries,1);
Compress = strings(totalEntries,1);
Time_s   = zeros(totalEntries,1);
MiB_s    = zeros(totalEntries,1);

idx = 1;
for o = 1:nLayouts
    for d = 1:nTypes
        for c = 1:nComps
            Layout(idx)   = cfg.order{o,1};
            DType(idx)    = cfg.dtype{d,1};
            Compress(idx) = cfg.comp{c};
            Time_s(idx)   = times(o,d,c);
            MiB_s(idx)    = speeds(o,d,c);
            idx = idx + 1;
        end
    end
end

T = table(Layout, DType, Compress, Time_s, MiB_s);
disp(T);

fprintf("\n🎉  all save_bl_tif tests passed\n");
end

%% ---------- helpers --------------------------------------------------------
function sandbox_cleanup(dirPath)
    fclose('all');
    safe_rmdir(dirPath);
end

function restore_rw(p)
    if exist(p,'file'), fileattrib(p,'+w'); end
end

function safe_rmdir(p)
    if exist(p,'dir')
        try
            rmdir(p,'s');
        catch
            pause(0.1);
            if exist(p,'dir'), rmdir(p,'s'); end
        end
    end
end
