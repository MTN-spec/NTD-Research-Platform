const { TabixIndexedFile } = require('@gmod/tabix');
const { RemoteFile, LocalFile } = require('generic-filehandle');
const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

async function getSlice(chrom, start, end, gene, localTbi) {
    const baseUrl = 'https://1000genomes.s3.amazonaws.com/release/20130502/';
    const vcfFile = `ALL.chr${chrom}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz`;

    console.log(`\n--- Slicing Real Data: ${gene} (Chr ${chrom}) ---`);
    console.log(`Region: ${chrom}:${start}-${end}`);
    console.log(`Using Local Index: ${localTbi}`);
    
    try {
        const tFile = new TabixIndexedFile({
            filehandle: new RemoteFile(baseUrl + vcfFile),
            tbiFilehandle: new LocalFile(localTbi),
        });

        const header = await tFile.getHeader();
        const lines = [];
        
        // Tabix region fetch
        await tFile.getLines(chrom, start, end, (line) => {
            lines.push(line);
        });

        console.log(`  Found ${lines.length} variants.`);
        
        const outputDir = path.join(__dirname, '..', 'data', 'raw');
        if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
        
        const outputPath = path.join(outputDir, `ALL.chr${chrom}.genotypes_${gene}.vcf.gz`);
        const fullVcf = header + '\n' + lines.join('\n') + '\n';
        
        const compressed = zlib.gzipSync(fullVcf);
        fs.writeFileSync(outputPath, compressed);
        
        console.log(`  Saved: ${outputPath}`);
    } catch (err) {
        console.error(`  Error in slicing ${gene}:`, err.message);
        throw err;
    }
}

async function main() {
    try {
        // DHFR: 5:79922047-79950802
        await getSlice('5', 79900000, 80000000, 'DHFR', path.join(__dirname, 'chr5.tbi'));
        // FOLR1: 11:71900602-71907367
        await getSlice('11', 71850000, 71950000, 'FOLR1', path.join(__dirname, 'chr11.tbi'));
        console.log('\n[SUCCESS] Real genomic slices extracted using local indices.');
    } catch (e) {
        process.exit(1);
    }
}

main();
