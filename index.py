
# http://localhost:5000/ 
# http://localhost:5000/diseases/0080927
# http://localhost:5000/diseases/9120
# http://localhost:5000/spsm?c1=9120&c2=4
# http://localhost:5000/diseases/4 http://localhost:5000/diseases/4/codes
# http://localhost:5000/diseases/9120/codes
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS



app = Flask(__name__)
CORS(app)
import rdflib
g = rdflib.Graph()
print("Parsing ontology...")
g.parse("Ontology\\HumanDO.nt")
print("Parsing ontology done. Ready...")
# app.run(debug=True,host='0.0.0.0')
treats={}
f=open("Ontology\\treat_data.csv")
lines=f.readlines()
for line in lines:
    flds=line.split(',')
    doid=flds[0][5:]
    drtype=flds[1].replace("\n", "")
    if treats.get(doid):
        treats[doid].append(drtype)
    else: treats[doid]=[drtype]


#===============================
@app.route('/')
def index():
    return render_template('index.html')
#===============================

#===============================
@app.route('/diseases/<id>')
def get_doid(id):
    print("get_doid:"+id)
    qry1="""
      prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?d ?Xrefs ?defn ?prntlbl ?name
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
            ?s rdfs:label ?name.
        ?s hdo:IAO_0000115 ?defn.
    }
    """

    qres = g.query(qry1)
    doid={}
    for row in qres:
        doid={}
        doid['name']=str(row.name);
        #doid['parent']=str(row.prntlbl);
        doid['defn']=str(row.defn);
 
    qry2="""
      prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?syn
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
            ?s obo:hasExactSynonym ?syn.
    }"""
    syns=[]
    qres = g.query(qry2)

    for row in qres:
        syns.append(str(row.syn))
    if len(syns)>0: doid['Synonyms']=syns
    qry3="""
      prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?Xref
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
            ?s obo:hasDbXref ?Xref.
    }"""
    Xrefs=[]
    qres = g.query(qry3)

    for row in qres:
        Xrefs.append(str(row.Xref))
    if len(Xrefs)>0: doid['Xrefs']=Xrefs
    qry2="""
    prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?x
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
            ?s obo:inSubset ?x.
    }"""
    subs=[]
    qres = g.query(qry2)

    for row in qres:
        subs.append(str(row.x))
    if len(subs)>0: doid['Subsets']=subs
    qry2="""
    prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select distinct ?prntlbl
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
             ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf>+ ?prnt.
        ?prnt rdfs:label ?prntlbl
    }"""
    prnts=[]
    qres = g.query(qry2)

    for row in qres:
        prnts.append(str(row.prntlbl))
    if len(prnts)>0: doid['Parents']=prnts
    # print(doid)

    if len(doid)>0 : 
        doid['id']='DOID:'+id;
        if treats.get(id):doid['treats']=treats[id]
             
        return jsonify(doid)
    else: return "DOID not found", 404;#abort(404)
#===============================



@app.route('/diseases/<id>/codes')
def get_doids(id):
    print("get_doids:"+id)
    qry1="""
      prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?d ?ch
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
        ?ch <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s.
    }
    """

    qres = g.query(qry1)
    doids=[]
    for row in qres:
        doids.append(str(row.ch))
    if len(doids)>0 : return jsonify(doids)  
    
def url2id(url):
    if url[-1]!='>': return(url[36:])
    return(url[36:-1])

def getDirectParent(id):
    qry="""
    prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?prnt 
    { ?s obo:id ?d.
        filter(str(?d)=\"DOID:"""+id +  """\").
             ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?prnt.
        }  """

    qres = g.query(qry)
    prnts=[]
    for row in qres:
        prnts.append(str(row.prnt))
    return(prnts)
    
def getPath(id):
    path=[]
    i=0
    crntid=id
    while 1==1 :
        pp=getDirectParent(crntid)        
        if len(pp)==0 : break;
        if len(pp)==1: crntid=url2id(pp[0])
        else: crntid=url2id(pp[1])
        path.append(crntid)
    return(path)

def Len2(c1,c2):
    p1=getPath(c1)#path doesnot include source
    p2=getPath(c2)
    ix=findLSOix(p1,p2)
    return(len(p1)+len(p2)-2*(ix+1))#
    
def findLSOix(p1,p2):
    ix=-1
    for i in range(min(len(p1),len(p2))):
        if p1[i]==p2[i]:ix=i
        else: break;
    return(ix)

def shortestPathMeasure(c1,c2):
    sim_path =2* 14- Len2( c1, c2)
    return(sim_path)
    
def findDeepMax():
    qry="""prefix hdo: <http://purl.obolibrary.org/obo/>
    prefix obo: <http://www.geneontology.org/formats/oboInOwl#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select  ?ch count(distinct ?prnt) as ?depth
    { ?s obo:id ?d.
        filter(str(?d)="DOID:4").
        ?ch <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ?s.
        filter not exists {?x <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?ch}.
        ?ch <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ?prnt.
    }group by ?ch        """
        
    sparql.setQuery(qry)
    sparql.setReturnFormat(JSON)
    result = sparql.query().convert()
    lvs=[]
    dpth=[]
    for row in result["results"]["bindings"]:
        #print(row["mnp"]["value"]) 
        lvs.append(row["ch"]["value"]) 
        dpth.append(row["depth"]["value"]) 
    print(len(lvs))
    mx=0
    for i in range(len(lvs)):
        #print(i,lvs[i])
        if int(dpth[i])>mx:
            pp=getPath(url2id(lvs[i]))
            if len(pp)>mx:
                print(lvs[i],len(pp))
                mx=len(pp)
    
    return(mx)
    
    
#===============================
@app.route('/spsm')#Shortest path semantic measure
def spsm():
   c1  = request.args.get('c1', None)
   c2  = request.args.get('c2', None)
   res = shortestPathMeasure(c1,c2)
   return(jsonify({'shortestPathMeasure':res}))