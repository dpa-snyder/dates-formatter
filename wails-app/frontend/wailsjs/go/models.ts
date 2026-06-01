export namespace main {
	
	export class ColumnsResult {
	    columns: string[];
	    rowCount: number;
	    dateyColumns: string[];
	
	    static createFrom(source: any = {}) {
	        return new ColumnsResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.columns = source["columns"];
	        this.rowCount = source["rowCount"];
	        this.dateyColumns = source["dateyColumns"];
	    }
	}
	export class ProcessOptions {
	    filePath: string;
	    columns: string[];
	    mode: number;
	    outputMode: string;
	    yyOverrideEnabled: boolean;
	    yyPrefix: string;
	
	    static createFrom(source: any = {}) {
	        return new ProcessOptions(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.filePath = source["filePath"];
	        this.columns = source["columns"];
	        this.mode = source["mode"];
	        this.outputMode = source["outputMode"];
	        this.yyOverrideEnabled = source["yyOverrideEnabled"];
	        this.yyPrefix = source["yyPrefix"];
	    }
	}
	export class Settings {
	    theme: string;
	    lastMode: number;
	    lastOutputMode: string;
	    recentFiles: string[];
	    windowWidth: number;
	    windowHeight: number;
	    yyOverrideEnabled: boolean;
	    yyPrefix: string;
	
	    static createFrom(source: any = {}) {
	        return new Settings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.theme = source["theme"];
	        this.lastMode = source["lastMode"];
	        this.lastOutputMode = source["lastOutputMode"];
	        this.recentFiles = source["recentFiles"];
	        this.windowWidth = source["windowWidth"];
	        this.windowHeight = source["windowHeight"];
	        this.yyOverrideEnabled = source["yyOverrideEnabled"];
	        this.yyPrefix = source["yyPrefix"];
	    }
	}

}

