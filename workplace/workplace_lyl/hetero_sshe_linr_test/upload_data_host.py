import os
import argparse
from pipeline.backend.pipeline import PipeLine

DATA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")  

def main(data_base=DATA_BASE):
    
    host = 10000

   
    partition = 4

    data = {"name": "hetero_sshe_linr_test_host", "namespace": f"test"}

    pipeline_upload = PipeLine().set_initiator(role="host", party_id=host).set_roles(host=host)

    pipeline_upload.add_upload_data(file=os.path.join(data_base, "hetero_sshe_linr_test_host.csv"),
                                    table_name=data["name"],            
                                    namespace=data["namespace"],         
                                    head=1, partition=partition)               

    pipeline_upload.upload(drop=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("PIPELINE DEMO")
    parser.add_argument("--base", "-b", type=str,
                        help="data base, path to directory that contains examples/data")

    args = parser.parse_args()
    if args.base is not None:
        main(args.base)
    else:
        main()
